from pathlib import Path

from flask import Blueprint, abort, current_app, jsonify, send_file, session

from ..auth import login_required, role_required
from ..db import get_db
from ..validators.common import json_body, clean_text

moderation_bp = Blueprint("moderation", __name__)


def committee_only(view):
    return login_required(role_required("Comitato", "Moderatore")(view))


@moderation_bp.get("/dashboard")
@committee_only
def dashboard():
    with get_db().cursor(dictionary=True) as cursor:
        cursor.execute("SELECT stato_pubblicazione, COUNT(*) AS totale FROM segnalazione GROUP BY stato_pubblicazione")
        reports = cursor.fetchall()
        cursor.execute("SELECT stato_verifica, COUNT(*) AS totale FROM utente GROUP BY stato_verifica")
        identities = cursor.fetchall()
        cursor.execute("SELECT COUNT(*) AS totale FROM analisi_ia WHERE stato='In attesa'")
        pending_ai = cursor.fetchone()["totale"]
    return jsonify(segnalazioni=reports, verifiche=identities, analisi_ia_in_attesa=pending_ai)


@moderation_bp.get("/verifiche")
@committee_only
def pending_verifications():
    with get_db().cursor(dictionary=True) as cursor:
        cursor.execute("SELECT i.id_identita,i.tipo_verifica,i.data_richiesta,u.id_utente,u.nome,u.cognome,u.email FROM identita i JOIN utente u ON u.id_utente=i.id_utente WHERE i.stato_verifica='In attesa' ORDER BY i.data_richiesta")
        return jsonify(items=cursor.fetchall())


@moderation_bp.patch("/verifiche/<int:verification_id>")
@committee_only
def review_verification(verification_id):
    data, error = json_body(("esito",))
    if error: return error
    outcome = data["esito"]
    if outcome not in ("Verificato", "Rifiutato"): abort(400, "Esito non valido.")
    connection = get_db()
    connection.start_transaction()
    with connection.cursor(dictionary=True) as cursor:
        cursor.execute("SELECT id_utente FROM identita WHERE id_identita=%s FOR UPDATE", (verification_id,))
        identity = cursor.fetchone()
        if not identity: connection.rollback(); abort(404, "Verifica non trovata.")
        cursor.execute("UPDATE identita SET stato_verifica=%s,data_verifica=NOW(),id_revisore=%s WHERE id_identita=%s", (outcome, session["user"]["id"], verification_id))
        cursor.execute("UPDATE utente SET stato_verifica=%s WHERE id_utente=%s", (outcome, identity["id_utente"]))
    connection.commit()
    return jsonify(message="Verifica aggiornata.")


@moderation_bp.get("/verifiche/<int:verification_id>/documenti/<lato>")
@committee_only
def get_identity_document(verification_id, lato):
    if lato not in ("fronte", "retro"): abort(404)
    with get_db().cursor(dictionary=True) as cursor:
        if lato == "fronte":
            cursor.execute("SELECT fronte AS percorso FROM identita WHERE id_identita=%s", (verification_id,))
        else:
            cursor.execute("SELECT retro AS percorso FROM identita WHERE id_identita=%s", (verification_id,))
        row = cursor.fetchone()
    if not row or not row["percorso"]: abort(404)
    root = (Path(current_app.config["UPLOAD_FOLDER"]) / "identity").resolve()
    path = Path(row["percorso"]).resolve()
    if root not in path.parents or not path.is_file(): abort(404)
    return send_file(path, as_attachment=True, download_name=f"identita-{verification_id}-{lato}")


@moderation_bp.post("/utenti/<int:user_id>/ban")
@committee_only
def ban_user(user_id):
    data, error = json_body(("motivo",))
    if error: return error
    reason = clean_text(data["motivo"], 500)
    if not reason: abort(400, "Motivazione obbligatoria.")
    if user_id == session["user"]["id"]: abort(403, "Non puoi bannare il tuo account.")
    connection = get_db()
    with connection.cursor(dictionary=True) as cursor:
        cursor.execute("SELECT u.id_utente,u.stato_account,r.nome_ruolo FROM utente u JOIN ruolo r ON r.id_ruolo=u.id_ruolo WHERE u.id_utente=%s", (user_id,))
        target = cursor.fetchone()
        if not target: abort(404, "Utente non trovato.")
        if target["nome_ruolo"] in ("Comitato", "Moderatore"): abort(403, "Non puoi bannare un account con privilegi di moderazione.")
        cursor.execute("UPDATE utente SET stato_account='Bannato' WHERE id_utente=%s", (user_id,))
        cursor.execute("INSERT INTO moderazione (id_moderatore,id_utente,tipo_intervento,motivazione) VALUES (%s,%s,'Ban',%s)", (session["user"]["id"], user_id, reason))
    connection.commit()
    return jsonify(message="Utente bannato.")


@moderation_bp.get("/analisi-ia")
@committee_only
def pending_ai_reviews():
    with get_db().cursor(dictionary=True) as cursor:
        cursor.execute("SELECT a.id_analisi,a.id_segnalazione,a.id_file,a.tipo_analisi,a.stato,a.modello,a.versione_modello,a.risultato,a.punteggio,a.data_creazione,s.titolo,s.descrizione FROM analisi_ia a JOIN segnalazione s ON s.id_segnalazione=a.id_segnalazione WHERE a.stato IN ('In attesa','Revisione richiesta','Errore') ORDER BY a.data_creazione LIMIT 100")
        return jsonify(items=cursor.fetchall())


@moderation_bp.patch("/analisi-ia/<int:analysis_id>")
@committee_only
def review_ai_result(analysis_id):
    data, error = json_body(("decisione",))
    if error: return error
    decision = clean_text(data["decisione"], 50)
    if decision not in ("Confermata", "Respinta", "Da rivedere"):
        abort(400, "Decisione non valida.")
    with get_db().cursor() as cursor:
        cursor.execute("UPDATE analisi_ia SET decisione_revisore=%s,id_revisore=%s,stato='Completata',data_completamento=NOW() WHERE id_analisi=%s", (decision, session["user"]["id"], analysis_id))
        if cursor.rowcount != 1: abort(404, "Analisi non trovata.")
    get_db().commit()
    return jsonify(message="Revisione registrata.")


@moderation_bp.patch("/segnalazioni/<int:report_id>/visibilita")
@committee_only
def change_visibility(report_id):
    data, error = json_body(("visibilita",))
    if error: return error
    visibility = data["visibilita"]
    if visibility not in ("Pubblicata", "Nascosta"): abort(400, "Valore di visibilità non valido.")
    with get_db().cursor() as cursor:
        cursor.execute("UPDATE segnalazione SET stato_pubblicazione=%s WHERE id_segnalazione=%s", (visibility, report_id))
        if cursor.rowcount != 1: abort(404, "Segnalazione non trovata.")
    get_db().commit()
    return jsonify(message="Visibilità aggiornata.")


@moderation_bp.get("/segnalazioni")
@committee_only
def moderation_reports():
    with get_db().cursor(dictionary=True) as cursor:
        cursor.execute("SELECT s.id_segnalazione,s.titolo,s.stato_pubblicazione,st.nome AS stato,s.data_creazione,u.nome,u.cognome FROM segnalazione s JOIN stato_segnalazione st ON st.id_stato=s.id_stato JOIN utente u ON u.id_utente=s.id_utente ORDER BY s.data_creazione DESC LIMIT 100")
        return jsonify(items=cursor.fetchall())


@moderation_bp.get("/utenti")
@committee_only
def moderation_users():
    with get_db().cursor(dictionary=True) as cursor:
        cursor.execute("SELECT id_utente,nome,cognome,email,stato_verifica,stato_account FROM utente ORDER BY data_registrazione DESC LIMIT 100")
        return jsonify(items=cursor.fetchall())


@moderation_bp.post("/quartieri")
@committee_only
def create_neighborhood():
    data, error = json_body(("nome",))
    if error: return error
    name = clean_text(data["nome"], 100)
    if not name: abort(400, "Nome quartiere non valido.")
    try:
        with get_db().cursor() as cursor:
            cursor.execute("INSERT INTO quartiere (nome) VALUES (%s)", (name,))
            neighborhood_id = cursor.lastrowid
        get_db().commit()
    except Exception:
        get_db().rollback()
        raise
    return jsonify(id_quartiere=neighborhood_id,nome=name), 201


@moderation_bp.patch("/quartieri/<int:neighborhood_id>")
@committee_only
def update_neighborhood(neighborhood_id):
    data, error = json_body()
    if error: return error
    name = clean_text(data.get("nome"), 100, required=False) if "nome" in data else None
    active = data.get("attivo") if "attivo" in data else None
    if name is None and active is None: abort(400, "Nessun dato da aggiornare.")
    if active is not None and not isinstance(active, bool): abort(400, "Valore attivo non valido.")
    with get_db().cursor() as cursor:
        cursor.execute("UPDATE quartiere SET nome=COALESCE(%s,nome),attivo=COALESCE(%s,attivo) WHERE id_quartiere=%s", (name, active, neighborhood_id))
        if cursor.rowcount != 1: abort(404, "Quartiere non trovato.")
    get_db().commit()
    return jsonify(message="Quartiere aggiornato.")


@moderation_bp.post("/categorie")
@committee_only
def create_category():
    data, error = json_body(("nome_categoria",))
    if error: return error
    name = clean_text(data["nome_categoria"], 100)
    if not name: abort(400, "Nome categoria non valido.")
    try:
        with get_db().cursor() as cursor:
            cursor.execute("INSERT INTO categoria (nome_categoria) VALUES (%s)", (name,))
            category_id = cursor.lastrowid
        get_db().commit()
    except Exception:
        get_db().rollback()
        raise
    return jsonify(id_categoria=category_id,nome_categoria=name), 201


@moderation_bp.patch("/categorie/<int:category_id>")
@committee_only
def update_category(category_id):
    data, error = json_body()
    if error: return error
    name = clean_text(data.get("nome_categoria"), 100, required=False) if "nome_categoria" in data else None
    active = data.get("attiva") if "attiva" in data else None
    if name is None and active is None: abort(400, "Nessun dato da aggiornare.")
    if active is not None and not isinstance(active, bool): abort(400, "Valore attivo non valido.")
    with get_db().cursor() as cursor:
        cursor.execute("UPDATE categoria SET nome_categoria=COALESCE(%s,nome_categoria),attiva=COALESCE(%s,attiva) WHERE id_categoria=%s", (name, active, category_id))
        if cursor.rowcount != 1: abort(404, "Categoria non trovata.")
    get_db().commit()
    return jsonify(message="Categoria aggiornata.")
