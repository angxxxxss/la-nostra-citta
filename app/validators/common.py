import re
from flask import request

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
CF_RE = re.compile(r"^[A-Z0-9]{16}$", re.IGNORECASE)


def json_body(required=()):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, ({"error": {"code": "INVALID_JSON", "message": "Il corpo deve essere un oggetto JSON."}}, 400)
    missing = [field for field in required if field not in data]
    if missing:
        return None, ({"error": {"code": "MISSING_FIELDS", "fields": missing}}, 400)
    return data, None


def clean_text(value, max_length, *, required=True):
    if not isinstance(value, str):
        return None
    value = value.strip()
    if (required and not value) or len(value) > max_length:
        return None
    return value
