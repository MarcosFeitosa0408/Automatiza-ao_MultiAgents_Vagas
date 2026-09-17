from sqlalchemy import inspect

import core.database as database


def test_initialize_database_creates_job_applications_table(
    monkeypatch,
):
    test_database_url = "sqlite+pysqlite:///:memory:"

    monkeypatch.setenv(
        "DATABASE_URL",
        test_database_url,
    )

    engine = database.create_database_engine()

    monkeypatch.setattr(
        database,
        "create_database_engine",
        lambda: engine,
    )

    database.initialize_database()

    inspector = inspect(engine)

    assert "job_applications" in inspector.get_table_names()
