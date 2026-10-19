from pathlib import Path

from flask import current_app, g
import mysql.connector
from mysql.connector import Error, pooling

_pool = None


def get_pool():
    global _pool
    if _pool is None:
        cfg = current_app.config
        host = cfg.get("DATABASE_HOST", "").strip()
        database = cfg.get("DATABASE_NAME", "").strip()
        user = cfg.get("DATABASE_USER", "").strip()
        password = cfg.get("DATABASE_PASSWORD", "")
        if not all((host, database, user, password)):
            raise RuntimeError(
                "Configura DATABASE_HOST, DATABASE_NAME, DATABASE_USER e DATABASE_PASSWORD "
                "nel file .env per collegarti al database MySQL remoto."
            )
        if host.lower() in {"localhost", "127.0.0.1", "::1"}:
            raise RuntimeError(
                "Il database locale non è supportato: imposta DATABASE_HOST con l'host del MySQL remoto."
            )

        connection_options = {
            "pool_name": "la_nostra_citta_pool",
            "pool_size": cfg["DATABASE_POOL_SIZE"],
            "host": host,
            "port": cfg["DATABASE_PORT"],
            "database": database,
            "user": user,
            "password": password,
            "charset": "utf8mb4",
            "collation": "utf8mb4_0900_ai_ci",
            "autocommit": False,
        }
        ssl_ca = cfg.get("DATABASE_SSL_CA", "").strip()
        if ssl_ca:
            if not Path(ssl_ca).is_file():
                raise RuntimeError("Il certificato DATABASE_SSL_CA non è stato trovato.")
            connection_options.update(
                ssl_ca=ssl_ca,
                ssl_verify_cert=True,
                ssl_verify_identity=True,
            )
        _pool = pooling.MySQLConnectionPool(**connection_options)
    return _pool


def get_db():
    if "db" not in g:
        connection = get_pool().get_connection()
        try:
            connection.ping(reconnect=True, attempts=1, delay=0)
        except Error:
            try:
                connection.close()
            except Error:
                pass
            connection = get_pool().get_connection()
            connection.ping(reconnect=True, attempts=1, delay=0)
        g.db = connection
    return g.db


def close_db(_error=None):
    connection = g.pop("db", None)
    if connection is not None:
        if connection.in_transaction:
            connection.rollback()
        try:
            connection.close()
        except Error:
            # A pooled connection can already be closed by the remote provider.
            pass


def reset_pool_for_tests():
    global _pool
    _pool = None
