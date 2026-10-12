"""Query SQL per account e autenticazione. Tutti i valori sono parametrizzati."""


def account_exists(cursor, email, codice_fiscale):
    cursor.execute("SELECT id_utente FROM utente WHERE email=%s OR codice_fiscale=%s LIMIT 1", (email, codice_fiscale))
    return cursor.fetchone() is not None


def citizen_role_id(cursor):
    cursor.execute("SELECT id_ruolo FROM ruolo WHERE nome_ruolo=%s", ("Cittadino",))
    row = cursor.fetchone()
    return row["id_ruolo"] if row else None


def insert_account(cursor, profile, password_hash, role_id):
    cursor.execute(
        "INSERT INTO utente (nome,cognome,codice_fiscale,email,password_hash,indirizzo,id_quartiere,stato_verifica,stato_account,id_ruolo) VALUES (%s,%s,%s,%s,%s,%s,%s,'In attesa','Attivo',%s)",
        (profile["nome"], profile["cognome"], profile["codice_fiscale"], profile["email"], password_hash, profile["indirizzo"], profile.get("id_quartiere"), role_id),
    )
    return cursor.lastrowid


def find_account_for_login(cursor, email):
    cursor.execute("SELECT u.id_utente,u.email,u.password_hash,u.stato_verifica,u.stato_account,r.nome_ruolo FROM utente u JOIN ruolo r ON r.id_ruolo=u.id_ruolo WHERE u.email=%s LIMIT 1", (email,))
    return cursor.fetchone()
