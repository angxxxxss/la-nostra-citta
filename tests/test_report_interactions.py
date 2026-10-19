from io import BytesIO
from pathlib import Path

from PIL import Image

from app.routes import reports
from app.repositories.report_repository import fetch_report


class MemoryCursor:
    def __init__(self, connection):
        self.connection = connection
        self.rowcount = 0
        self.lastrowid = None
        self.result = None
        self.rows = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, sql, params=()):
        self.rowcount = 0
        self.result = None
        self.rows = []
        if sql.startswith("SELECT id_segnalazione FROM segnalazione"):
            self.result = (params[0],)
        elif sql.startswith("INSERT IGNORE INTO sostegno"):
            value = tuple(params)
            if value not in self.connection.supports:
                self.connection.supports.add(value)
                self.rowcount = 1
        elif sql.startswith("DELETE FROM sostegno"):
            value = tuple(params)
            if value in self.connection.supports:
                self.connection.supports.remove(value)
                self.rowcount = 1
        elif sql.startswith("SELECT id_utente FROM segnalazione"):
            self.result = {"id_utente": self.connection.owner}
        elif sql.startswith("SELECT COUNT(*) AS totale FROM file_multimediale"):
            self.result = {"totale": self.connection.existing_media + len(self.connection.media)}
        elif sql.startswith("INSERT INTO file_multimediale"):
            self.connection.media.append(params)
            self.lastrowid = len(self.connection.media)
            self.rowcount = 1
        elif sql.startswith("SELECT f.percorso FROM file_multimediale"):
            index = params[0] - 1
            self.result = {"percorso": self.connection.media[index][2]} if 0 <= index < len(self.connection.media) else None
        elif sql.startswith("INSERT INTO commento"):
            self.connection.comments.append({
                "id_commento": len(self.connection.comments) + 1,
                "testo": params[0],
                "nome": "Test",
                "cognome": "Utente",
            })
            self.lastrowid = len(self.connection.comments)
            self.rowcount = 1
        elif sql.startswith("SELECT c.id_commento,c.testo"):
            self.rows = self.connection.comments[:]
        else:
            raise AssertionError(f"Query imprevista nel test: {sql}")

    def fetchone(self):
        return self.result

    def fetchall(self):
        return self.rows


class MemoryConnection:
    def __init__(self, owner=7, existing_media=0):
        self.owner = owner
        self.existing_media = existing_media
        self.supports = set()
        self.media = []
        self.comments = []
        self.commits = 0
        self.rollbacks = 0

    def cursor(self, **_kwargs):
        return MemoryCursor(self)

    def start_transaction(self):
        pass

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


def sign_in(client, user_id=7):
    with client.session_transaction() as session:
        session["user"] = {"id": user_id, "role": "Cittadino", "verified": True}


def png_file():
    output = BytesIO()
    Image.new("RGB", (3, 3), "red").save(output, "PNG")
    output.seek(0)
    return output.getvalue()


def test_vote_can_be_added_and_removed(client, monkeypatch):
    connection = MemoryConnection()
    monkeypatch.setattr(reports, "get_db", lambda: connection)
    monkeypatch.setattr(reports, "require_verified", lambda: None)
    sign_in(client)

    path = "/api/segnalazioni/4/sostegni"
    assert client.post(path, json={"tipo": "Sostegno"}).status_code == 201
    assert (7, 4, "Sostegno") in connection.supports
    assert client.delete(path + "/Sostegno").status_code == 204
    assert (7, 4, "Sostegno") not in connection.supports
    assert client.post(path, json={"tipo": "Sostegno"}).status_code == 201


def test_report_exposes_only_the_viewers_own_vote():
    class ReportCursor:
        def execute(self, sql, _params):
            self.sql = sql

        def fetchone(self):
            return {"id_segnalazione": 4, "titolo": "Lampione spento"}

        def fetchall(self):
            if "FROM file_multimediale" in self.sql or "FROM categoria" in self.sql:
                return []
            if "GROUP BY tipo" in self.sql:
                return [{"tipo": "Sostegno", "totale": 2}]
            if "AND id_utente=" in self.sql:
                return [{"tipo": "Sostegno"}]
            raise AssertionError(self.sql)

    own = fetch_report(ReportCursor(), 4, viewer_id=7)
    guest = fetch_report(ReportCursor(), 4)
    assert own["sostegni"] == {"Sostegno": 2}
    assert own["sostegni_utente"] == ["Sostegno"]
    assert guest["sostegni_utente"] == []


def test_comment_is_saved_and_visible(client, monkeypatch):
    connection = MemoryConnection()
    monkeypatch.setattr(reports, "get_db", lambda: connection)
    monkeypatch.setattr(reports, "require_verified", lambda: None)
    sign_in(client)

    path = "/api/segnalazioni/4/commenti"
    created = client.post(path, json={"testo": "Serve un intervento"})
    assert created.status_code == 201
    assert created.json["id_commento"] == 1
    listed = client.get(path)
    assert listed.status_code == 200
    assert listed.json["items"][0]["testo"] == "Serve un intervento"


def test_author_can_add_photo_and_read_it(client, app, monkeypatch):
    connection = MemoryConnection()
    monkeypatch.setattr(reports, "get_db", lambda: connection)
    monkeypatch.setattr(reports, "require_verified", lambda: None)
    sign_in(client)

    image = png_file()
    response = client.post(
        "/api/segnalazioni/4/allegati",
        data={"allegati": (BytesIO(image), "foto.png")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 201
    assert response.json["file_ids"] == [1]
    assert connection.media[0][0] == 4
    assert connection.media[0][3] == "image/png"
    assert client.get("/api/segnalazioni/4/allegati/1").data == image


def test_photo_upload_rejects_other_authors_and_limit(client, app, monkeypatch):
    connection = MemoryConnection(owner=8)
    monkeypatch.setattr(reports, "get_db", lambda: connection)
    monkeypatch.setattr(reports, "require_verified", lambda: None)
    sign_in(client)
    path = "/api/segnalazioni/4/allegati"

    forbidden = client.post(path, data={"allegati": (BytesIO(png_file()), "foto.png")})
    assert forbidden.status_code == 404
    assert not list((Path(app.config["UPLOAD_FOLDER"]) / "media").glob("*"))

    connection.owner = 7
    connection.existing_media = 5
    full = client.post(path, data={"allegati": (BytesIO(png_file()), "foto.png")})
    assert full.status_code == 400
    assert full.json["error"]["code"] == "TOO_MANY_FILES"
    assert not list((Path(app.config["UPLOAD_FOLDER"]) / "media").glob("*"))
