"""Contas e dados privados persistentes do MVP local (SQLite)."""
import hashlib
import os
import secrets
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException
from pwdlib import PasswordHash
from core.schemas.candidate import MasterProfile
from core.schemas.job_application import JobApplicationObject

password_hash = PasswordHash.recommended()
_dummy_hash = password_hash.hash(secrets.token_urlsafe(32))
SESSION_SECONDS = 8 * 60 * 60


def empty_profile(user_id: str, name: str, email: str) -> MasterProfile:
    return MasterProfile.model_validate({
        'schema_version': '1.0', 'candidate_id': user_id,
        'candidate': {
            'name': name, 'email': email, 'phone': '',
            'location': dict(city='', state='', country=''),
            'employment_status': dict(currently_clt=False, actively_seeking=False, priority='', primary_goal=''),
            'career_target': dict(primary_roles=[], secondary_roles=[], seniority=[]),
            'work_preferences': dict(employment_type_priority=[], remote=False, hybrid=False, onsite=False, preferred_location=[], relocation=False),
        },
        'professional_positioning': dict(title='', summary='', focus=[]),
        'education': [], 'experience': [], 'projects': [],
        'skills': {key: [] for key in ('core', 'database', 'python', 'analytics', 'tools', 'automation')},
        'languages': dict(portuguese='', english=''),
        'portfolio': dict(portfolio_url='', github_url='', linkedin_url=''),
        'evidence_policy': {
            **{key: True for key in ('master_profile_is_source_of_truth', 'never_invent_skill', 'never_invent_experience', 'never_invent_education', 'never_invent_certification', 'never_invent_result', 'never_invent_salary', 'never_invent_job')},
            'unknown_value': 'NAO_IDENTIFICADO',
        },
    })


class AccountStore:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL, password_hash TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS sessions (
                    token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL,
                    expires_at REAL NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id));
                CREATE TABLE IF NOT EXISTS profiles (
                    user_id TEXT PRIMARY KEY, payload TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id));
                CREATE TABLE IF NOT EXISTS private_applications (
                    user_id TEXT NOT NULL, application_id TEXT NOT NULL,
                    payload TEXT NOT NULL, PRIMARY KEY(user_id, application_id),
                    FOREIGN KEY(user_id) REFERENCES users(id));
                CREATE TABLE IF NOT EXISTS attempts (
                    bucket TEXT NOT NULL, occurred_at REAL NOT NULL);
                CREATE INDEX IF NOT EXISTS attempts_bucket ON attempts(bucket, occurred_at);
            ''')

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        try:
            with db:
                yield db
        finally:
            db.close()

    def limit(self, bucket: str, maximum: int = 20):
        now = time.time()
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('DELETE FROM attempts WHERE occurred_at < ?', (now - 900,))
            count = db.execute('SELECT COUNT(*) FROM attempts WHERE bucket=?', (bucket,)).fetchone()[0]
            if count >= maximum:
                raise HTTPException(429, 'Muitas tentativas. Aguarde 15 minutos.', headers={'Retry-After': '900'})
            db.execute('INSERT INTO attempts VALUES (?, ?)', (bucket, now))

    def create_user(self, name: str, email: str, password: str):
        user_id = str(uuid4())
        hashed = password_hash.hash(password)
        profile = empty_profile(user_id, name, email)
        try:
            with self.connection() as db:
                db.execute('INSERT INTO users VALUES (?, ?, ?, ?)', (user_id, email, name, hashed))
                db.execute('INSERT INTO profiles VALUES (?, ?)', (user_id, profile.model_dump_json()))
        except sqlite3.IntegrityError:
            raise HTTPException(409, 'Não foi possível cadastrar com esse e-mail.') from None
        return dict(id=user_id, name=name, email=email)

    def check_password(self, email: str, password: str):
        with self.connection() as db:
            row = db.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
        valid = password_hash.verify(password, row['password_hash'] if row else _dummy_hash)
        if not row or not valid:
            raise HTTPException(401, 'E-mail ou senha incorretos.')
        return {key: row[key] for key in ('id', 'name', 'email')}

    def issue_session(self, user_id: str):
        token = secrets.token_urlsafe(48)
        with self.connection() as db:
            db.execute('DELETE FROM sessions WHERE expires_at <= ?', (time.time(),))
            db.execute('INSERT INTO sessions VALUES (?, ?, ?)', (hashlib.sha256(token.encode()).hexdigest(), user_id, time.time() + SESSION_SECONDS))
        return token

    def current_user(self, token: str):
        with self.connection() as db:
            row = db.execute('''SELECT u.id, u.name, u.email FROM sessions s
                JOIN users u ON u.id=s.user_id WHERE s.token_hash=? AND s.expires_at>?''',
                (hashlib.sha256(token.encode()).hexdigest(), time.time())).fetchone()
        if not row:
            raise HTTPException(401, 'Entre na sua conta para continuar.', headers={'WWW-Authenticate': 'Bearer'})
        return dict(row)

    def revoke(self, token: str):
        with self.connection() as db:
            db.execute('DELETE FROM sessions WHERE token_hash=?', (hashlib.sha256(token.encode()).hexdigest(),))


def get_store() -> AccountStore:
    return AccountStore(os.getenv('ACCOUNT_DATABASE_PATH', 'data/private/accounts.sqlite3'))


class AccountMemoryAgent:
    def __init__(self, store: AccountStore, user_id: str):
        self.store, self.user_id = store, user_id

    def load_profile(self):
        with self.store.connection() as db:
            row = db.execute('SELECT payload FROM profiles WHERE user_id=?', (self.user_id,)).fetchone()
        if not row:
            raise FileNotFoundError('Perfil não cadastrado.')
        return MasterProfile.model_validate_json(row['payload'])

    get_profile = load_profile

    def save_profile(self, profile: MasterProfile):
        profile = MasterProfile.model_validate(profile.model_dump())
        profile = profile.model_copy(update={'candidate_id': self.user_id})
        with self.store.connection() as db:
            db.execute('INSERT INTO profiles VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET payload=excluded.payload',
                       (self.user_id, profile.model_dump_json()))
        return profile

    def get_candidate_name(self):
        return self.get_profile().candidate.name

    def get_primary_roles(self):
        return self.get_profile().candidate.career_target.primary_roles

    def get_core_skills(self):
        return self.get_profile().skills.core


class AccountJobRepository:
    def __init__(self, store: AccountStore, user_id: str):
        self.store, self.user_id = store, user_id

    def save(self, application: JobApplicationObject):
        with self.store.connection() as db:
            db.execute('''INSERT INTO private_applications VALUES (?, ?, ?)
                ON CONFLICT(user_id, application_id) DO UPDATE SET payload=excluded.payload''',
                (self.user_id, application.application_id, application.model_dump_json()))
        return application

    def get(self, application_id: str):
        with self.store.connection() as db:
            row = db.execute('SELECT payload FROM private_applications WHERE user_id=? AND application_id=?',
                             (self.user_id, application_id)).fetchone()
        return JobApplicationObject.model_validate_json(row['payload']) if row else None

    def list_all(self):
        with self.store.connection() as db:
            rows = db.execute('SELECT payload FROM private_applications WHERE user_id=? ORDER BY application_id', (self.user_id,)).fetchall()
        return [JobApplicationObject.model_validate_json(row['payload']) for row in rows]

    def delete(self, application_id: str):
        with self.store.connection() as db:
            cursor = db.execute('DELETE FROM private_applications WHERE user_id=? AND application_id=?', (self.user_id, application_id))
        return cursor.rowcount > 0
