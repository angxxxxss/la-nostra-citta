"""Query di lettura per segnalazioni; i valori ricevuti arrivano sempre come parametri SQL."""


def fetch_report(cursor, report_id):
    cursor.execute("""SELECT s.id_segnalazione,s.titolo,s.descrizione,s.data_creazione,
        s.latitudine,s.longitudine,s.id_utente,s.stato_pubblicazione,st.nome AS stato,
        l.indirizzo,q.nome AS quartiere,u.nome,u.cognome
        FROM segnalazione s JOIN stato_segnalazione st ON st.id_stato=s.id_stato
        JOIN luogo l ON l.id_luogo=s.id_luogo JOIN quartiere q ON q.id_quartiere=l.id_quartiere
        JOIN utente u ON u.id_utente=s.id_utente WHERE s.id_segnalazione=%s""", (report_id,))
    item = cursor.fetchone()
    if not item:
        return None
    cursor.execute("SELECT id_file,tipo,mime_type,coordinate_exif FROM file_multimediale WHERE id_segnalazione=%s ORDER BY id_file", (report_id,))
    item["allegati"] = cursor.fetchall()
    cursor.execute("SELECT c.id_categoria,c.nome_categoria FROM categoria c JOIN segnalazione_categoria sc ON sc.id_categoria=c.id_categoria WHERE sc.id_segnalazione=%s", (report_id,))
    item["categorie"] = cursor.fetchall()
    cursor.execute("SELECT tipo,COUNT(*) AS totale FROM sostegno WHERE id_segnalazione=%s GROUP BY tipo", (report_id,))
    item["sostegni"] = {row["tipo"]: row["totale"] for row in cursor.fetchall()}
    return item


def fetch_account_status(cursor, user_id):
    cursor.execute("SELECT stato_verifica,stato_account FROM utente WHERE id_utente=%s", (user_id,))
    return cursor.fetchone()
