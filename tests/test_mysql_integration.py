"""Test opt-in del vincolo anti-duplicato su un database di test separato.

Impostare RUN_MYSQL_INTEGRATION=1 e DATABASE_NAME=la_nostra_citta_test dopo aver
applicato schema.sql e initial_data.sql. Il test rifiuta database non di test.
"""
import os
import pytest
import mysql.connector
from mysql.connector import IntegrityError


@pytest.mark.skipif(os.getenv("RUN_MYSQL_INTEGRATION") != "1", reason="test MySQL opt-in")
def test_duplicate_support_is_rejected_by_database():
    database_name = os.getenv("DATABASE_TEST_NAME", "la_nostra_citta_test")
    if "test" not in database_name.lower():
        pytest.fail("Il test di integrazione può usare solo un database con 'test' nel nome.")
    connection = mysql.connector.connect(
        host=os.getenv("DATABASE_HOST", "127.0.0.1"),
        port=int(os.getenv("DATABASE_PORT", "3306")),
        user=os.getenv("DATABASE_USER", "root"),
        password=os.getenv("DATABASE_PASSWORD", ""),
        database=database_name,
    )
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT id_ruolo FROM ruolo WHERE nome_ruolo='Cittadino'")
        role_id = cursor.fetchone()[0]
        cursor.execute("SELECT id_quartiere FROM quartiere LIMIT 1")
        neighborhood_id = cursor.fetchone()[0]
        suffix = os.urandom(5).hex()
        cursor.execute("INSERT INTO utente (nome,cognome,codice_fiscale,email,password_hash,indirizzo,id_quartiere,id_ruolo) VALUES ('Test','Utente',%s,%s,'hash','Via Test',%s,%s)", (suffix.upper().ljust(16, 'A')[:16], f'{suffix}@example.test', neighborhood_id, role_id))
        user_id = cursor.lastrowid
        cursor.execute("SELECT id_stato FROM stato_segnalazione WHERE nome='Ricevuta'")
        status_id = cursor.fetchone()[0]
        cursor.execute("INSERT INTO luogo (indirizzo,id_quartiere) VALUES ('Via Test',%s)", (neighborhood_id,))
        place_id = cursor.lastrowid
        cursor.execute("INSERT INTO segnalazione (titolo,descrizione,id_utente,id_luogo,id_stato,stato_pubblicazione) VALUES ('Test','Test',%s,%s,%s,'Bozza')", (user_id, place_id, status_id))
        report_id = cursor.lastrowid
        cursor.execute("INSERT INTO file_multimediale (id_segnalazione,tipo,percorso,mime_type,dimensione,sha256) VALUES (%s,'Foto','test.jpg','image/jpeg',1,REPEAT('a',64))", (report_id,))
        cursor.execute("UPDATE segnalazione SET stato_pubblicazione='Pubblicata' WHERE id_segnalazione=%s", (report_id,))
        cursor.execute("INSERT INTO sostegno (id_utente,id_segnalazione,tipo) VALUES (%s,%s,'Sostegno')", (user_id, report_id))
        with pytest.raises(IntegrityError):
            cursor.execute("INSERT INTO sostegno (id_utente,id_segnalazione,tipo) VALUES (%s,%s,'Sostegno')", (user_id, report_id))
        connection.rollback()
    finally:
        cursor.close()
        connection.close()
