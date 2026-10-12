"""Regole di accesso per operazioni che richiedono un cittadino verificato."""
from ..repositories.report_repository import fetch_account_status


class AccountNotActive(Exception):
    pass


class IdentityNotVerified(Exception):
    pass


def assert_verified_user(cursor, user_id):
    account = fetch_account_status(cursor, user_id)
    if not account or account["stato_account"] != "Attivo":
        raise AccountNotActive
    if account["stato_verifica"] != "Verificato":
        raise IdentityNotVerified
