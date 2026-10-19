import hashlib
import json
from pathlib import Path

from flask import Blueprint, abort, current_app, jsonify, request, send_file, session

from ..auth import login_required, role_required
from ..db import get_db
from ..uploads import exif_coordinates, save_private_upload, validate_report_media
from ..validators.common import clean_text, json_body
from ..services.ai_pipeline import enqueue_report_analyses
from ..services.report_service import assert_verified_user, AccountNotActive, IdentityNotVerified
from ..repositories.report_repository import fetch_report

reports_bp = Blueprint("reports", __name__)


def save_report_media(files):
    """Valida e salva i file, eliminando quelli già scritti se uno fallisce."""
    stored = []
    current_path = None
    try:
        for file in files:
            mime = validate_report_media(file)
            current_path = save_private_upload(file, current_app.config["UPLOAD_FOLDER"], "media", lambda f, expected=mime: expected)
            file_size = Path(current_path).stat().st_size
            if file_size > current_app.config["MAX_CONTENT_LENGTH"]:
                raise ValueError("File troppo grande.")
            digest = hashlib.sha256(Path(current_path).read_bytes()).hexdigest()
            exif_lat, exif_lon = exif_coordinates(current_path) if mime.startswith("image/") else (None, None)
            stored.append((current_path, mime, exif_lat, exif_lon, file_size, digest))
            current_path = None
    except Exception:
        if current_path:
            Path(current_path).unlink(missing_ok=True)
        for path, *_ in stored:
            Path(path).unlink(missing_ok=True)
        raise
    return stored


def insert_report_media(cursor, report_id, stored):
    ids = []
    for path, mime, exif_lat, exif_lon, file_size, digest in stored:
        cursor.execute("INSERT INTO file_multimediale (id_segnalazione,tipo,percorso,mime_type,dimensione,sha256,coordinate_exif) VALUES (%s,%s,%s,%s,%s,%s,%s)", (report_id, "Foto" if mime.startswith("image/") else "Video", path, mime, file_size, digest, json.dumps({"latitudine": exif_lat, "longitudine": exif_lon}) if exif_lat is not None and exif_lon is not None else None))
        ids.append(cursor.lastrowid)
    return ids


def require_verified():
    user = session.get("user")
    if not user:
        abort(401, "Autenticazione richiesta.")
    try:
        with get_db().cursor(dictionary=True) as cursor:
            assert_verified_user(cursor, user["id"])
    except AccountNotActive:
        abort(403, "Account non attivo.")
    except IdentityNotVerified:
        abort(403, "Completa la verifica dell'identità prima di interagire.")
    get_db().commit()


@reports_bp.get("/quartieri")
def neighborhoods():
    with get_db().cursor(dictionary=True) as cursor:
        cursor.execute("SELECT id_quartiere, nome FROM quartiere ORDER BY nome")
        return jsonify(items=cursor.fetchall())


@reports_bp.get("/categorie")
def categories():
    with get_db().cursor(dictionary=True) as cursor:
        cursor.execute("SELECT id_categoria, nome_categoria FROM categoria WHERE attiva=1 ORDER BY nome_categoria")
        return jsonify(items=cursor.fetchall())


@reports_bp.get("/segnalazioni")
def list_reports():
    page = max(1, request.args.get("page", 1, type=int))
    limit = min(50, max(1, request.args.get("limit", 20, type=int)))
    neighborhood_id = request.args.get("quartiere", type=int)
    state_id = request.args.get("stato", type=int)
    category_id = request.args.get("categoria", type=int)
    query_text = request.args.get("q", "")[:100].strip()
    term = f"%{query_text}%" if query_text else None
    query = """SELECT s.id_segnalazione FROM segnalazione s JOIN luogo l ON l.id_luogo=s.id_luogo
        WHERE s.stato_pubblicazione='Pubblicata'
          AND (%s IS NULL OR l.id_quartiere=%s)
          AND (%s IS NULL OR s.id_stato=%s)
          AND (%s IS NULL OR EXISTS (SELECT 1 FROM segnalazione_categoria sc WHERE sc.id_segnalazione=s.id_segnalazione AND sc.id_categoria=%s))
          AND (%s IS NULL OR s.titolo LIKE %s OR s.descrizione LIKE %s)
        ORDER BY s.data_creazione DESC LIMIT %s OFFSET %s"""
    params = (neighborhood_id, neighborhood_id, state_id, state_id, category_id, category_id, term, term, term, limit, (page - 1) * limit)
    with get_db().cursor(dictionary=True) as cursor:
        cursor.execute(query, params)
        ids = [row["id_segnalazione"] for row in cursor.fetchall()]
        viewer_id = (session.get("user") or {}).get("id")
        items = [fetch_report(cursor, report_id, viewer_id) for report_id in ids]
    return jsonify(items=items, page=page, limit=limit)


@reports_bp.get("/segnalazioni/priorita")
def priorities():
    with get_db().cursor(dictionary=True) as cursor:
        cursor.execute("""SELECT s.id_segnalazione, s.titolo,
            COALESCE(SUM(so.tipo='Sostegno'),0) AS sostenitori,
            COALESCE(SUM(so.tipo='Interesse'),0) AS interessati FROM segnalazione s LEFT JOIN sostegno so
            ON so.id_segnalazione=s.id_segnalazione WHERE s.stato_pubblicazione='Pubblicata'
            GROUP BY s.id_segnalazione ORDER BY sostenitori DESC, interessati DESC, s.data_creazione DESC LIMIT 50""")
        return jsonify(items=cursor.fetchall())


@reports_bp.get("/segnalazioni/<int:report_id>")
def get_report(report_id):
    with get_db().cursor(dictionary=True) as cursor:
        item = fetch_report(cursor, report_id, (session.get("user") or {}).get("id"))
    if not item or item["stato_pubblicazione"] != "Pubblicata":
        user = session.get("user")
        if not item or not user or (user["id"] != item["id_utente"] and user["role"] not in ("Comitato", "Moderatore")):
            abort(404, "Segnalazione non trovata.")
    return jsonify(item=item)


@reports_bp.post("/segnalazioni")
@login_required
def create_report():
    require_verified()
    title = clean_text(request.form.get("titolo"), 150)
    description = clean_text(request.form.get("descrizione"), 5000)
    address = clean_text(request.form.get("indirizzo"), 180)
    neighborhood_id = request.form.get("id_quartiere", type=int)
    if not title or not description or not address or not neighborhood_id:
        return jsonify(error={"code": "INVALID_REPORT", "message": "Titolo, descrizione, indirizzo e quartiere sono obbligatori."}), 400
    files = request.files.getlist("allegati")
    if not files or any(not f.filename for f in files):
        return jsonify(error={"code": "ATTACHMENT_REQUIRED", "message": "Allega almeno una foto o un video."}), 400
    if len(files) > 5:
        return jsonify(error={"code": "TOO_MANY_FILES", "message": "Puoi allegare al massimo 5 file."}), 400
    try:
        lat = float(request.form["latitudine"]) if request.form.get("latitudine") else None
        lon = float(request.form["longitudine"]) if request.form.get("longitudine") else None
    except ValueError:
        return jsonify(error={"code": "INVALID_COORDINATES", "message": "Coordinate non valide."}), 400
    if (lat is None) != (lon is None) or (lat is not None and not (-90 <= lat <= 90 and -180 <= lon <= 180)):
        return jsonify(error={"code": "INVALID_COORDINATES", "message": "Inserisci entrambe le coordinate entro i limiti geografici."}), 400
    stored = []
    try:
        stored = save_report_media(files)
        if lat is None and stored:
            for _, mime, exif_lat, exif_lon, *_ in stored:
                if mime.startswith("image/") and exif_lat is not None and exif_lon is not None:
                    lat, lon = exif_lat, exif_lon
                    break
        connection = get_db()
        connection.start_transaction()
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT id_quartiere FROM quartiere WHERE id_quartiere=%s AND attivo=1", (neighborhood_id,))
            if not cursor.fetchone():
                connection.rollback()
                for path, *_ in stored: Path(path).unlink(missing_ok=True)
                return jsonify(error={"code": "INVALID_NEIGHBORHOOD", "message": "Quartiere non valido."}), 400
            cursor.execute("INSERT INTO luogo (indirizzo, id_quartiere) VALUES (%s,%s)", (address, neighborhood_id))
            place_id = cursor.lastrowid
            cursor.execute("SELECT id_stato FROM stato_segnalazione WHERE nome='Ricevuta' LIMIT 1")
            status = cursor.fetchone()
            if not status:
                raise RuntimeError("Stati iniziali del database non caricati.")
            cursor.execute("INSERT INTO segnalazione (titolo, descrizione, id_utente, id_luogo, id_stato, stato_pubblicazione, latitudine, longitudine) VALUES (%s,%s,%s,%s,%s,'Bozza',%s,%s)", (title, description, session["user"]["id"], place_id, status["id_stato"], lat, lon))
            report_id = cursor.lastrowid
            insert_report_media(cursor, report_id, stored)
            category_ids = request.form.getlist("categorie", type=int)
            for category_id in set(category_ids):
                cursor.execute("INSERT IGNORE INTO segnalazione_categoria (id_segnalazione,id_categoria,origine) SELECT %s,id_categoria,'utente' FROM categoria WHERE id_categoria=%s AND attiva=1", (report_id, category_id))
            cursor.execute("UPDATE segnalazione SET stato_pubblicazione='Pubblicata' WHERE id_segnalazione=%s", (report_id,))
            cursor.execute("INSERT INTO storico_stato (id_segnalazione,id_stato_precedente,id_stato_nuovo,id_utente,nota) VALUES (%s,NULL,%s,%s,%s)", (report_id, status["id_stato"], session["user"]["id"], "Segnalazione pubblicata"))
            enqueue_report_analyses(cursor, report_id)
        connection.commit()
    except ValueError as error:
        for path, *_ in stored:
            Path(path).unlink(missing_ok=True)
        return jsonify(error={"code": "INVALID_ATTACHMENT", "message": str(error)}), 400
    except Exception:
        get_db().rollback()
        for path, *_ in stored:
            Path(path).unlink(missing_ok=True)
        raise
    return jsonify(message="Segnalazione pubblicata.", id_segnalazione=report_id), 201


@reports_bp.post("/segnalazioni/<int:report_id>/allegati")
@login_required
def add_report_media(report_id):
    require_verified()
    files = request.files.getlist("allegati")
    if not files or any(not file.filename for file in files):
        return jsonify(error={"code": "ATTACHMENT_REQUIRED", "message": "Scegli almeno una foto o un video."}), 400
    if len(files) > 5:
        return jsonify(error={"code": "TOO_MANY_FILES", "message": "Puoi allegare al massimo 5 file per segnalazione."}), 400
    stored = []
    connection = None
    try:
        stored = save_report_media(files)
        connection = get_db()
        connection.start_transaction()
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT id_utente FROM segnalazione WHERE id_segnalazione=%s AND stato_pubblicazione='Pubblicata' FOR UPDATE", (report_id,))
            report = cursor.fetchone()
            if not report or report["id_utente"] != session["user"]["id"]:
                abort(404, "Segnalazione non trovata o non di tua proprietà.")
            cursor.execute("SELECT COUNT(*) AS totale FROM file_multimediale WHERE id_segnalazione=%s", (report_id,))
            if cursor.fetchone()["totale"] + len(stored) > 5:
                connection.rollback()
                for path, *_ in stored:
                    Path(path).unlink(missing_ok=True)
                return jsonify(error={"code": "TOO_MANY_FILES", "message": "Una segnalazione può contenere al massimo 5 file."}), 400
            file_ids = insert_report_media(cursor, report_id, stored)
        connection.commit()
    except ValueError as error:
        if connection is not None:
            connection.rollback()
        for path, *_ in stored:
            Path(path).unlink(missing_ok=True)
        return jsonify(error={"code": "INVALID_ATTACHMENT", "message": str(error)}), 400
    except Exception:
        if connection is not None:
            connection.rollback()
        for path, *_ in stored:
            Path(path).unlink(missing_ok=True)
        raise
    return jsonify(message="Allegati aggiunti.", file_ids=file_ids), 201


@reports_bp.patch("/segnalazioni/<int:report_id>")
@login_required
def edit_report(report_id):
    require_verified()
    data, error = json_body()
    if error:
        return error
    title = clean_text(data.get("titolo"), 150, required=False) if "titolo" in data else None
    description = clean_text(data.get("descrizione"), 5000, required=False) if "descrizione" in data else None
    if "titolo" in data and title is None or "descrizione" in data and description is None:
        return jsonify(error={"code": "INVALID_REPORT", "message": "Titolo o descrizione non validi."}), 400
    if title is None and description is None:
        return jsonify(error={"code": "NO_CHANGES", "message": "Nessun dato da aggiornare."}), 400
    with get_db().cursor() as cursor:
        cursor.execute("UPDATE segnalazione SET titolo=COALESCE(%s,titolo), descrizione=COALESCE(%s,descrizione) WHERE id_segnalazione=%s AND id_utente=%s", (title, description, report_id, session["user"]["id"]))
        if cursor.rowcount != 1:
            abort(404, "Segnalazione non trovata o non di tua proprietà.")
    get_db().commit()
    return jsonify(message="Segnalazione aggiornata.")


@reports_bp.delete("/segnalazioni/<int:report_id>")
@login_required
def delete_report(report_id):
    connection = get_db()
    paths = []
    connection.start_transaction()
    with connection.cursor(dictionary=True) as cursor:
        cursor.execute("SELECT percorso FROM file_multimediale f JOIN segnalazione s ON s.id_segnalazione=f.id_segnalazione WHERE s.id_segnalazione=%s AND s.id_utente=%s FOR UPDATE", (report_id, session["user"]["id"]))
        paths = [row["percorso"] for row in cursor.fetchall()]
        cursor.execute("DELETE FROM segnalazione WHERE id_segnalazione=%s AND id_utente=%s", (report_id, session["user"]["id"]))
        if cursor.rowcount != 1:
            connection.rollback()
            abort(404, "Segnalazione non trovata o non di tua proprietà.")
    connection.commit()
    for path in paths:
        Path(path).unlink(missing_ok=True)
    return "", 204


@reports_bp.get("/segnalazioni/<int:report_id>/allegati/<int:file_id>")
def get_media(report_id, file_id):
    with get_db().cursor(dictionary=True) as cursor:
        cursor.execute("SELECT f.percorso FROM file_multimediale f JOIN segnalazione s ON s.id_segnalazione=f.id_segnalazione WHERE f.id_file=%s AND f.id_segnalazione=%s AND s.stato_pubblicazione='Pubblicata'", (file_id, report_id))
        row = cursor.fetchone()
    if not row:
        abort(404)
    media_root = (Path(current_app.config["UPLOAD_FOLDER"]) / "media").resolve()
    file_path = Path(row["percorso"]).resolve()
    if media_root not in file_path.parents or not file_path.is_file():
        abort(404)
    return send_file(file_path, conditional=True, max_age=3600)


@reports_bp.post("/segnalazioni/<int:report_id>/commenti")
@login_required
def create_comment(report_id):
    require_verified()
    data, error = json_body(("testo",))
    if error: return error
    text = clean_text(data["testo"], 2000)
    if not text: return jsonify(error={"code": "INVALID_COMMENT", "message": "Commento vuoto o troppo lungo."}), 400
    with get_db().cursor() as cursor:
        cursor.execute("INSERT INTO commento (testo,id_utente,id_segnalazione) SELECT %s,%s,%s FROM segnalazione WHERE id_segnalazione=%s AND stato_pubblicazione='Pubblicata'", (text, session["user"]["id"], report_id, report_id))
        if cursor.rowcount != 1: abort(404, "Segnalazione non trovata.")
        comment_id = cursor.lastrowid
    get_db().commit()
    return jsonify(id_commento=comment_id), 201


@reports_bp.get("/segnalazioni/<int:report_id>/commenti")
def list_comments(report_id):
    with get_db().cursor(dictionary=True) as cursor:
        cursor.execute("SELECT c.id_commento,c.testo,c.data,c.modificato_il,u.nome,u.cognome FROM commento c JOIN utente u ON u.id_utente=c.id_utente JOIN segnalazione s ON s.id_segnalazione=c.id_segnalazione WHERE c.id_segnalazione=%s AND c.cancellato=0 AND s.stato_pubblicazione='Pubblicata' ORDER BY c.data", (report_id,))
        return jsonify(items=cursor.fetchall())


@reports_bp.patch("/commenti/<int:comment_id>")
@login_required
def edit_comment(comment_id):
    data, error = json_body(("testo",))
    if error: return error
    text = clean_text(data["testo"], 2000)
    if not text: return jsonify(error={"code": "INVALID_COMMENT", "message": "Commento vuoto o troppo lungo."}), 400
    with get_db().cursor() as cursor:
        cursor.execute("UPDATE commento SET testo=%s, modificato_il=NOW() WHERE id_commento=%s AND id_utente=%s AND cancellato=0", (text, comment_id, session["user"]["id"]))
        if cursor.rowcount != 1: abort(404, "Commento non trovato o non di tua proprietà.")
    get_db().commit()
    return jsonify(message="Commento aggiornato.")


@reports_bp.delete("/commenti/<int:comment_id>")
@login_required
def delete_comment(comment_id):
    with get_db().cursor() as cursor:
        cursor.execute("UPDATE commento SET cancellato=1 WHERE id_commento=%s AND id_utente=%s AND cancellato=0", (comment_id, session["user"]["id"]))
        if cursor.rowcount != 1: abort(404, "Commento non trovato o non di tua proprietà.")
    get_db().commit()
    return "", 204


@reports_bp.post("/segnalazioni/<int:report_id>/sostegni")
@login_required
def add_support(report_id):
    require_verified()
    data, error = json_body(("tipo",))
    if error: return error
    kind = data["tipo"]
    if kind not in ("Sostegno", "Interesse"):
        return jsonify(error={"code": "INVALID_SUPPORT", "message": "Tipo di interazione non valido."}), 400
    with get_db().cursor() as cursor:
        cursor.execute("SELECT id_segnalazione FROM segnalazione WHERE id_segnalazione=%s AND stato_pubblicazione='Pubblicata'", (report_id,))
        if not cursor.fetchone(): abort(404, "Segnalazione non trovata.")
        cursor.execute("INSERT IGNORE INTO sostegno (id_utente,id_segnalazione,tipo) VALUES (%s,%s,%s)", (session["user"]["id"], report_id, kind))
        if cursor.rowcount != 1:
            get_db().rollback()
            return jsonify(error={"code": "ALREADY_RECORDED", "message": "Hai già registrato questo tipo di sostegno."}), 409
    get_db().commit()
    return jsonify(message="Interazione registrata."), 201


@reports_bp.delete("/segnalazioni/<int:report_id>/sostegni/<tipo>")
@login_required
def remove_support(report_id, tipo):
    if tipo not in ("Sostegno", "Interesse"): abort(400, "Tipo non valido.")
    with get_db().cursor() as cursor:
        cursor.execute("DELETE FROM sostegno WHERE id_utente=%s AND id_segnalazione=%s AND tipo=%s", (session["user"]["id"], report_id, tipo))
    get_db().commit()
    return "", 204


@reports_bp.patch("/segnalazioni/<int:report_id>/stato")
@login_required
@role_required("Comitato", "Moderatore")
def update_status(report_id):
    data, error = json_body(("stato",))
    if error: return error
    state = clean_text(data["stato"], 50)
    if state not in ("In valutazione", "Presa in carico", "Inviata ai candidati", "Conclusa", "Rifiutata"):
        return jsonify(error={"code": "INVALID_STATE", "message": "Transizione di stato non valida."}), 400
    connection = get_db()
    connection.start_transaction()
    with connection.cursor(dictionary=True) as cursor:
        cursor.execute("SELECT id_stato,nome FROM stato_segnalazione WHERE nome=%s", (state,))
        next_state = cursor.fetchone()
        cursor.execute("SELECT s.id_stato,st.nome FROM segnalazione s JOIN stato_segnalazione st ON st.id_stato=s.id_stato WHERE s.id_segnalazione=%s FOR UPDATE", (report_id,))
        old_state = cursor.fetchone()
        if not next_state or not old_state:
            connection.rollback(); abort(404, "Segnalazione o stato non trovato.")
        allowed = {"Ricevuta": {"In valutazione", "Rifiutata"}, "In valutazione": {"Presa in carico", "Rifiutata"}, "Presa in carico": {"Inviata ai candidati", "Conclusa", "Rifiutata"}, "Inviata ai candidati": {"Conclusa"}}
        if next_state["nome"] not in allowed.get(old_state["nome"], set()):
            connection.rollback(); abort(409, "Transizione di stato non consentita.")
        cursor.execute("UPDATE segnalazione SET id_stato=%s WHERE id_segnalazione=%s", (next_state["id_stato"], report_id))
        cursor.execute("INSERT INTO storico_stato (id_segnalazione,id_stato_precedente,id_stato_nuovo,id_utente,nota) VALUES (%s,%s,%s,%s,%s)", (report_id, old_state["id_stato"], next_state["id_stato"], session["user"]["id"], clean_text(data.get("nota", ""), 500, required=False)))
    connection.commit()
    return jsonify(message="Stato aggiornato.")


@reports_bp.get("/segnalazioni/<int:report_id>/storico")
def report_history(report_id):
    with get_db().cursor(dictionary=True) as cursor:
        cursor.execute("SELECT h.data_modifica,h.nota,nuovo.nome AS stato,u.nome,u.cognome FROM storico_stato h JOIN stato_segnalazione nuovo ON nuovo.id_stato=h.id_stato_nuovo JOIN utente u ON u.id_utente=h.id_utente JOIN segnalazione s ON s.id_segnalazione=h.id_segnalazione WHERE h.id_segnalazione=%s AND s.stato_pubblicazione='Pubblicata' ORDER BY h.data_modifica", (report_id,))
        return jsonify(items=cursor.fetchall())

