from flask import current_app, g
import mysql.connector
from mysql.connector import pooling

_pool = None


def get_pool():
    global _pool
    if _pool is None:
        cfg = current_app.config
        _pool = pooling.MySQLConnectionPool(
            pool_name="la_nostra_citta_pool",
            pool_size=cfg["DATABASE_POOL_SIZE"],
            host=cfg["DATABASE_HOST"],
            port=cfg["DATABASE_PORT"],
            database=cfg["DATABASE_NAME"],
            user=cfg["DATABASE_USER"],
            password=cfg["DATABASE_PASSWORD"],
            charset="utf8mb4",
            collation="utf8mb4_0900_ai_ci",
            autocommit=False,
        )
    return _pool


def get_db():
    if "db" not in g:
        g.db = get_pool().get_connection()
    return g.db


def close_db(_error=None):
    connection = g.pop("db", None)
    if connection is not None:
        if connection.in_transaction:
            connection.rollback()
        connection.close()


def reset_pool_for_tests():
    global _pool
    _pool = None
