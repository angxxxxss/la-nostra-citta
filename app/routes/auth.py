from pathlib import Path
from flask import Blueprint, current_app, jsonify, request, session
from mysql.connector import IntegrityError
from flask_limiter.util import get_remote_address

from .. import limiter
from ..auth import login_required, regenerate_session
from ..db import get_db
from ..validators.common import CF_RE, EMAIL_RE, clean_text, json_body
from ..uploads import validate_image_or_document, save_private_upload
from ..services.auth_service import AccountAlreadyExists, MissingCitizenRole, authenticate, register_account

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
@limiter.limit("5 per hour", key_func=get_remote_address)
def register():
    data, error = json_body(("nome", "cognome", "codice_fiscale", "email", "indirizzo", "password"))
    if error:
        return error
    nome = clean_text(data["nome"], 50)
    cognome = clean_text(data["cognome"], 50)
    indirizzo = clean_text(data["indirizzo"], 150)
    cf = clean_text(data["codice_fiscale"], 16)
    email = clean_text(data["email"], 254)
    password = data["password"]
    if not all((nome, cognome, indirizzo, cf, email)) or not CF_RE.fullmatch(cf) or not EMAIL_RE.fullmatch(email):
        return jsonify(error={"code": "INVALID_PROFILE", "message": "Controlla nome, cognome, codice fiscale, e-mail e indirizzo."}), 400
    if not isinstance(password, str) or len(password) < 12 or len(password) > 128:
        return jsonify(error={"code": "INVALID_PASSWORD", "message": "La password deve contenere da 12 a 128 caratteri."}), 400
    neighborhood_id = data.get("id_quartiere") or None
    if neighborhood_id is not None:
        try: neighborhood_id = int(neighborhood_id)
        except (TypeError, ValueError): return jsonify(error={"code": "INVALID_NEIGHBORHOOD", "message": "Quartiere non valido."}), 400
        with get_db().cursor() as cursor:
            cursor.execute("SELECT id_quartiere FROM quartiere WHERE id_quartiere=%s AND attivo=1", (neighborhood_id,))
            if not cursor.fetchone(): return jsonify(error={"code": "INVALID_NEIGHBORHOOD", "message": "Quartiere non valido."}), 400
    connection = get_db()
    profile = {"nome": nome, "cognome": cognome, "codice_fiscale": cf.upper(), "email": email.lower(), "indirizzo": indirizzo, "id_quartiere": neighborhood_id, "password": password}
    try:
        user_id = register_account(connection, profile)
        connection.commit()
    except AccountAlreadyExists:
        return jsonify(error={"code": "ACCOUNT_EXISTS", "message": "E-mail o codice fiscale già registrati."}), 409
    except MissingCitizenRole:
        return jsonify(error={"code": "CONFIGURATION_ERROR", "message": "Ruolo cittadino non inizializzato."}), 500
    except IntegrityError as error:
        connection.rollback()
        if error.errno == 1062:
            return jsonify(error={"code": "ACCOUNT_EXISTS", "message": "E-mail o codice fiscale già registrati."}), 409
        raise
    except Exception:
        connection.rollback()
        raise
    return jsonify(message="Account creato. Completa la verifica dell'identità prima di pubblicare.", user_id=user_id), 201


@auth_bp.post("/login")
@limiter.limit("10 per 15 minutes", key_func=get_remote_address)
def login():
    data, error = json_body(("email", "password"))
    if error:
        return error
    email = clean_text(data["email"], 254)
    password = data["password"]
    if not email or not EMAIL_RE.fullmatch(email) or not isinstance(password, str):
        return jsonify(error={"code": "INVALID_CREDENTIALS", "message": "Credenziali non valide."}), 401
    user = authenticate(get_db(), email.lower(), password)
    if not user:
        return jsonify(error={"code": "INVALID_CREDENTIALS", "message": "Credenziali non valide."}), 401
    if user.get("blocked"):
        return jsonify(error={"code": "ACCOUNT_BLOCKED", "message": "Account sospeso o bannato."}), 403
    regenerate_session()
    session["user"] = user
    return jsonify(user=session["user"])


@auth_bp.post("/logout")
@login_required
def logout():
    session.clear()
    return "", 204


@auth_bp.get("/me")
@login_required
def me():
    return jsonify(user=session["user"])


@auth_bp.post("/verify-document")
@login_required
def verify_document():
    if session["user"].get("verified"):
        return jsonify(error={"code": "ALREADY_VERIFIED", "message": "Identità già verificata."}), 409
    method = request.form.get("tipo_verifica", "")
    if method not in ("Carta identita", "SPID", "CIE"):
        return jsonify(error={"code": "INVALID_METHOD", "message": "Metodo di verifica non valido."}), 400
    if method in ("SPID", "CIE"):
        return jsonify(error={"code": "PROVIDER_NOT_CONFIGURED", "message": "Il flusso SPID/CIE richiede un identity provider accreditato e credenziali non ancora configurate."}), 501
    front, back = request.files.get("fronte"), request.files.get("retro")
    if not front or not back:
        return jsonify(error={"code": "DOCUMENTS_REQUIRED", "message": "Carica fronte e retro della carta d'identità."}), 400
    existing_paths = []
    with get_db().cursor(dictionary=True) as cursor:
        cursor.execute("SELECT fronte,retro FROM identita WHERE id_utente=%s", (session["user"]["id"],))
        existing = cursor.fetchone()
        if existing:
            existing_paths = [path for path in (existing["fronte"], existing["retro"]) if path]
    front_path = save_private_upload(front, current_app.config["UPLOAD_FOLDER"], "identity", validate_image_or_document)
    try:
        back_path = save_private_upload(back, current_app.config["UPLOAD_FOLDER"], "identity", validate_image_or_document)
    except Exception:
        Path(front_path).unlink(missing_ok=True)
        raise
    connection = get_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO identita (id_utente, tipo_verifica, fronte, retro, stato_verifica) VALUES (%s,%s,%s,%s,'In attesa') ON DUPLICATE KEY UPDATE tipo_verifica=VALUES(tipo_verifica), fronte=VALUES(fronte), retro=VALUES(retro), stato_verifica='In attesa', data_verifica=NULL", (session["user"]["id"], method, front_path, back_path))
        connection.commit()
    except Exception:
        connection.rollback()
        Path(front_path).unlink(missing_ok=True)
        Path(back_path).unlink(missing_ok=True)
        raise
    for old_path in existing_paths:
        Path(old_path).unlink(missing_ok=True)
    return jsonify(message="Documenti inviati al comitato per la verifica."), 202
