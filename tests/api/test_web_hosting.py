import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from core import web_hosting


def test_hosting_serves_only_dist_and_preserves_api(tmp_path, monkeypatch):
    monkeypatch.setenv("SERVE_FRONTEND", "1")
    monkeypatch.setenv("ACCOUNT_DATABASE_URL", "postgresql://unused/test")
    monkeypatch.setattr(web_hosting, "__file__", str(tmp_path / "core/web_hosting.py"))
    dist = tmp_path / "frontend/dist"
    dist.mkdir(parents=True)
    (dist / "index.html").write_text("<h1>Login</h1>")
    (tmp_path / ".env").write_text("PRIVATE")
    app = FastAPI()

    @app.get("/profile")
    def profile():
        raise HTTPException(401, "Entre na sua conta")

    web_hosting.configure_web_hosting(app)
    with TestClient(app) as client:
        assert client.get("/").text == "<h1>Login</h1>"
        assert client.get("/profile").status_code == 401
        for path in ("/.env", "/data/private/accounts.sqlite3", "/main.py", "/missing-api"):
            assert client.get(path).status_code == 404


def test_public_hosting_requires_postgres(monkeypatch):
    monkeypatch.setenv("SERVE_FRONTEND", "1")
    monkeypatch.delenv("ACCOUNT_DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="ACCOUNT_DATABASE_URL"):
        web_hosting.configure_web_hosting(FastAPI())


def test_local_api_does_not_require_compiled_frontend(monkeypatch):
    monkeypatch.delenv("SERVE_FRONTEND", raising=False)
    app = FastAPI()
    web_hosting.configure_web_hosting(app)
    assert not any(getattr(route, "name", None) == "frontend" for route in app.routes)
