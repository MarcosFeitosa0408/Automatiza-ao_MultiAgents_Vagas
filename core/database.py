import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.models import Base


def create_database_engine():
    """Cria a engine do banco configurado pela variável DATABASE_URL."""

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError(
            "DATABASE_URL não configurada."
        )

    return create_engine(
        database_url,
        pool_pre_ping=True,
    )


def create_session_factory():
    """Cria a fábrica de sessões do banco de dados."""

    engine = create_database_engine()

    return sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )


def initialize_database() -> None:
    """Cria no banco as tabelas definidas pelos modelos SQLAlchemy."""

    engine = create_database_engine()
    Base.metadata.create_all(engine)
