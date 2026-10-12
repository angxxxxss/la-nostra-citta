"""Contratto per i worker IA futuri; nessun modello esterno è invocato in questa versione."""

SUPPORTED_ANALYSES = ("moderazione_testo", "classificazione", "estrazione_exif", "verifica_multimediale")


def enqueue_report_analyses(cursor, report_id):
    """Registra attività pendenti nella stessa transazione della segnalazione."""
    for analysis_type in ("moderazione_testo", "classificazione", "verifica_multimediale"):
        cursor.execute(
            "INSERT INTO analisi_ia (id_segnalazione,tipo_analisi,stato) VALUES (%s,%s,'In attesa')",
            (report_id, analysis_type),
        )
