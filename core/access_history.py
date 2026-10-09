"""Historico de cadastro e entrada, sem senhas ou tokens."""
import time
from uuid import uuid4


def ensure_access_history(db):
    db.execute("""
        CREATE TABLE IF NOT EXISTS account_entry_history (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            event TEXT NOT NULL CHECK (event IN ('REGISTER', 'LOGIN')),
            occurred_at DOUBLE PRECISION NOT NULL
        )
    """)


def record_access_event(db, user_id, event):
    if event not in ('REGISTER', 'LOGIN'):
        raise ValueError('Evento de acesso invalido.')
    ensure_access_history(db)
    db.execute(
        'INSERT INTO account_entry_history '
        '(id, user_id, event, occurred_at) VALUES (?, ?, ?, ?)',
        (str(uuid4()), user_id, event, time.time()),
    )
