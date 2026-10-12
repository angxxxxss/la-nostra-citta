from io import BytesIO

from argon2 import PasswordHasher
from PIL import Image
from werkzeug.datastructures import FileStorage

from app.auth import verify_password
from app.uploads import validate_report_media


def test_home_renders_application(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Le priorit\xc3\xa0 di Milano" in response.data
    assert b"report-form" in response.data


def test_api_requires_authentication(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.json["error"]["code"] == "UNAUTHORIZED"


def test_register_rejects_missing_profile_before_database_access(client):
    response = client.post("/api/auth/register", json={"email": "x@example.test"})
    assert response.status_code == 400
    assert response.json["error"]["code"] == "MISSING_FIELDS"


def test_login_rejects_invalid_email_before_database_access(client):
    response = client.post("/api/auth/login", json={"email": "not-an-email", "password": "whatever"})
    assert response.status_code == 401
    assert response.json["error"]["code"] == "INVALID_CREDENTIALS"


def test_password_hash_verification():
    hasher = PasswordHasher()
    password_hash = hasher.hash("correct horse battery staple")
    assert verify_password(password_hash, "correct horse battery staple")
    assert not verify_password(password_hash, "wrong password")


def test_upload_checks_real_file_content():
    image = Image.new("RGB", (2, 2), "red")
    output = BytesIO()
    image.save(output, format="PNG")
    output.seek(0)
    upload = FileStorage(stream=output, filename="photo.jpg", content_type="image/jpeg")
    assert validate_report_media(upload) == "image/png"


def test_upload_rejects_unsupported_content():
    upload = FileStorage(stream=BytesIO(b"not a real image"), filename="photo.jpg", content_type="image/jpeg")
    try:
        validate_report_media(upload)
    except ValueError as error:
        assert "Formato file" in str(error)
    else:
        raise AssertionError("Il file non valido doveva essere respinto")


def test_csrf_protects_mutating_requests(tmp_path):
    from app import create_app
    secure_app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret-key-that-is-long-enough-123456",
        "SESSION_FILE_DIR": str(tmp_path / "secure-sessions"),
        "UPLOAD_FOLDER": str(tmp_path / "secure-uploads"),
        "RATELIMIT_ENABLED": False,
        "WTF_CSRF_ENABLED": True,
    })
    response = secure_app.test_client().post("/api/auth/login", json={"email": "a@example.test", "password": "password"})
    assert response.status_code == 400
    assert response.json["error"]["code"] == "CSRF_FAILED"
