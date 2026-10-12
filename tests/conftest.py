import pytest
from app import create_app


@pytest.fixture()
def app(tmp_path):
    return create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test-secret-key-that-is-long-enough-123456",
        "SESSION_FILE_DIR": str(tmp_path / "sessions"),
        "UPLOAD_FOLDER": str(tmp_path / "uploads"),
        "RATELIMIT_ENABLED": False,
    })


@pytest.fixture()
def client(app):
    return app.test_client()
