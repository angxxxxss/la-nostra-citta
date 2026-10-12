from functools import wraps
from flask import abort, current_app, session
from argon2 import PasswordHasher, Type
from argon2.exceptions import VerifyMismatchError, VerificationError

password_hasher = PasswordHasher(type=Type.ID)


def hash_password(password):
    return password_hasher.hash(password)


def verify_password(password_hash, password):
    try:
        return password_hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, TypeError):
        return False


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user"):
            abort(401, "Autenticazione richiesta.")
        return view(*args, **kwargs)
    return wrapped


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = session.get("user")
            if not user:
                abort(401, "Autenticazione richiesta.")
            if user.get("role") not in roles:
                abort(403, "Permessi insufficienti.")
            return view(*args, **kwargs)
        return wrapped
    return decorator


def regenerate_session():
    interface = current_app.session_interface
    regenerate = getattr(interface, "regenerate", None)
    if regenerate:
        regenerate(session)
    session.clear()
    session.permanent = True
