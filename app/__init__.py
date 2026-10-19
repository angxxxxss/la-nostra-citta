from pathlib import Path

from flask import Flask, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_session import Session
from flask_wtf.csrf import CSRFError, CSRFProtect, generate_csrf
from werkzeug.exceptions import HTTPException

from .config import Config
from .db import close_db, get_db

csrf = CSRFProtect()
session_ext = Session()
limiter = Limiter(key_func=get_remote_address, default_limits=[])


def create_app(test_config=None):
    app = Flask(__name__, static_folder="../static", template_folder="../templates")
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)
    if app.config["ENVIRONMENT"] == "production":
        secret = app.config["SECRET_KEY"]
        if len(secret) < 32 or secret.startswith(("replace-", "development-only")):
            raise RuntimeError("Definisci una SECRET_KEY casuale e non di esempio per la produzione.")
        if not app.config["SESSION_COOKIE_SECURE"]:
            raise RuntimeError("SESSION_COOKIE_SECURE deve essere true in produzione (HTTPS).")
        if not app.config["REDIS_URL"]:
            raise RuntimeError("Configura REDIS_URL per sessioni e rate limit persistenti in produzione.")
        app.config["SESSION_TYPE"] = "redis"

    Path(app.config["SESSION_FILE_DIR"]).mkdir(parents=True, exist_ok=True)
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
    if app.config["SESSION_TYPE"] == "redis":
        from redis import Redis
        app.config["SESSION_REDIS"] = Redis.from_url(app.config["REDIS_URL"])
    session_ext.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    app.teardown_appcontext(close_db)

    from .routes.web import web_bp
    from .routes.auth import auth_bp
    from .routes.reports import reports_bp
    from .routes.moderation import moderation_bp

    app.register_blueprint(web_bp)
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(reports_bp, url_prefix="/api")
    app.register_blueprint(moderation_bp, url_prefix="/api/moderation")

    @app.cli.command("promote-moderator")
    def promote_moderator():
        """Promuove un account esistente a moderatore; comando solo locale/operativo."""
        import click
        email = click.prompt("E-mail dell'account da promuovere")
        with get_db().cursor() as cursor:
            cursor.execute("UPDATE utente SET id_ruolo=(SELECT id_ruolo FROM ruolo WHERE nome_ruolo='Moderatore') WHERE email=%s", (email.lower(),))
            if cursor.rowcount != 1:
                click.echo("Account non trovato o ruolo invariato.")
                return
        get_db().commit()
        click.echo("Ruolo moderatore assegnato.")

    @app.get("/api/csrf")
    def csrf_token():
        return jsonify({"csrf_token": generate_csrf()})

    @app.get("/api/health")
    def health():
        from .db import get_db
        try:
            with get_db().cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return jsonify({"status": "ok", "database": "connected"})
        except Exception:
            return jsonify({"status": "degraded", "database": "unavailable"}), 503

    @app.errorhandler(CSRFError)
    def handle_csrf_error(error):
        return jsonify({"error": {"code": "CSRF_FAILED", "message": "Token CSRF mancante o non valido."}}), 400

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        return jsonify({"error": {"code": error.name.upper().replace(" ", "_"), "message": error.description}}), error.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        app.logger.exception("Errore non gestito")
        return jsonify({"error": {"code": "INTERNAL_ERROR", "message": "Errore interno del server."}}), 500

    @app.after_request
    def security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Content-Security-Policy", "default-src 'self'; script-src 'self' https://unpkg.com; style-src 'self' https://unpkg.com 'unsafe-inline'; img-src 'self' data: blob: https://unpkg.com https://*.tile.openstreetmap.org; media-src 'self'; connect-src 'self' https://unpkg.com https://*.tile.openstreetmap.org; object-src 'none'; base-uri 'self'; frame-ancestors 'none'")
        return response

    return app
