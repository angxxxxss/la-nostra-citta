"""Regole di dominio per creazione account e autenticazione."""
from ..auth import hash_password, verify_password
from ..repositories.auth_repository import account_exists, citizen_role_id, find_account_for_login, insert_account


class AccountAlreadyExists(Exception):
    pass


class MissingCitizenRole(Exception):
    pass


def register_account(connection, profile):
    try:
        with connection.cursor(dictionary=True) as cursor:
            if account_exists(cursor, profile["email"], profile["codice_fiscale"]):
                raise AccountAlreadyExists
            role_id = citizen_role_id(cursor)
            if role_id is None:
                raise MissingCitizenRole
            password_hash = hash_password(profile["password"])
            return insert_account(cursor, profile, password_hash, role_id)
    except Exception:
        connection.rollback()
        raise


def authenticate(connection, email, password):
    with connection.cursor(dictionary=True) as cursor:
        user = find_account_for_login(cursor, email)
    if not user or not verify_password(user["password_hash"], password):
        return None
    if user["stato_account"] != "Attivo":
        return {"blocked": True}
    return {
        "id": user["id_utente"],
        "email": user["email"],
        "role": user["nome_ruolo"],
        "verified": user["stato_verifica"] == "Verificato",
    }
