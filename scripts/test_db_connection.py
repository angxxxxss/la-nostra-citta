"""Verifica in sola lettura la connessione al MySQL configurato nel file .env."""

import os
import sys
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv
from mysql.connector import Error


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def main() -> int:
    host = os.getenv("DATABASE_HOST", "").strip()
    port_text = os.getenv("DATABASE_PORT", "3306").strip()
    database = os.getenv("DATABASE_NAME", "").strip()
    user = os.getenv("DATABASE_USER", "").strip()
    password = os.getenv("DATABASE_PASSWORD", "")
    ssl_ca = os.getenv("DATABASE_SSL_CA", "").strip()

    missing = [
        name
        for name, value in (
            ("DATABASE_HOST", host),
            ("DATABASE_NAME", database),
            ("DATABASE_USER", user),
            ("DATABASE_PASSWORD", password),
        )
        if not value
    ]
    if missing:
        print("Parametri mancanti nel .env: " + ", ".join(missing))
        return 2

    if host.lower() in {"localhost", "127.0.0.1", "::1"}:
        print("DATABASE_HOST punta al computer locale. Inserisci l'host del MySQL remoto.")
        return 2

    try:
        port = int(port_text)
    except ValueError:
        print("DATABASE_PORT deve essere un numero, ad esempio 3306.")
        return 2

    options = {
        "host": host,
        "port": port,
        "database": database,
        "user": user,
        "password": password,
        "connection_timeout": 10,
    }
    if ssl_ca:
        ca_path = Path(ssl_ca)
        if not ca_path.is_absolute():
            ca_path = PROJECT_ROOT / ca_path
        if not ca_path.is_file():
            print(f"Certificato CA non trovato: {ca_path}")
            return 2
        options.update(
            ssl_ca=str(ca_path),
            ssl_verify_cert=True,
            ssl_verify_identity=True,
        )

    print(f"Connessione a {host}:{port}, database {database}, utente {user}…")
    connection = None
    try:
        connection = mysql.connector.connect(**options)
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION(), DATABASE(), CURRENT_USER()")
            version, selected_database, current_user = cursor.fetchone()
        print("Connessione riuscita.")
        print(f"MySQL: {version}")
        print(f"Database: {selected_database}")
        print(f"Utente autenticato: {current_user}")
        return 0
    except Error as error:
        print(f"Connessione non riuscita ({error.__class__.__name__}): {error}")
        print("Controlla host, porta, credenziali, accesso di rete e certificato SSL nel .env.")
        return 1
    finally:
        if connection is not None and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    sys.exit(main())
