"""Serve somente a interface compilada, apos registrar as rotas da API."""
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles


def configure_web_hosting(app: FastAPI) -> None:
    if os.getenv("SERVE_FRONTEND", "0") != "1":
        return
    database_url = os.getenv("ACCOUNT_DATABASE_URL", "").strip()
    if not database_url.startswith(("postgresql://", "postgres://")):
        raise RuntimeError("Configure ACCOUNT_DATABASE_URL para hospedar a plataforma.")
    directory = Path(__file__).resolve().parents[1] / "frontend" / "dist"
    if not (directory / "index.html").is_file():
        raise RuntimeError("Compile a interface antes de iniciar a hospedagem.")
    app.mount("/", StaticFiles(directory=directory, html=True), name="frontend")
