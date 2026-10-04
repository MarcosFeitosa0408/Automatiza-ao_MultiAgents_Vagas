"""Contas privadas: SQLite local ou Postgres configurado explicitamente."""
import hashlib
import os
import secrets
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4
from functools import lru_cache

import psycopg

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
                CREATE TABLE IF NOT EXISTS account_access (
                    user_id TEXT PRIMARY KEY REFERENCES users(id),
                    state TEXT NOT NULL CHECK(state IN ('pending', 'active', 'blocked')),
                    role TEXT NOT NULL CHECK(role IN ('user', 'admin')));
                CREATE TABLE IF NOT EXISTS admin_audit (
                    id TEXT PRIMARY KEY, actor_id TEXT NOT NULL,
                    target_id TEXT NOT NULL, action TEXT NOT NULL,
                    occurred_at REAL NOT NULL);
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
                db.execute('INSERT INTO account_access VALUES (?, ?, ?)', (user_id, 'pending', 'user'))
        except (sqlite3.IntegrityError, psycopg.errors.UniqueViolation):
            raise HTTPException(409, 'Não foi possível cadastrar com esse e-mail.') from None
        return dict(id=user_id, name=name, email=email, role='user', state='pending')

    def check_password(self, email: str, password: str):
        with self.connection() as db:
            row = db.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
        valid = password_hash.verify(password, row['password_hash'] if row else _dummy_hash)
        if not row or not valid:
            raise HTTPException(401, 'E-mail ou senha incorretos.')
        with self.connection() as db:
            access = self._user(db, row['id'])
        if access['state'] != 'active':
            message = 'Sua conta aguarda autorização do administrador.' if access['state'] == 'pending' else 'Seu acesso foi bloqueado pelo administrador.'
            raise HTTPException(403, message)
        return access

    def issue_session(self, user_id: str):
        token = secrets.token_urlsafe(48)
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            user = self._user(db, user_id)
            if not user or user['state'] != 'active':
                raise HTTPException(403, 'Esta conta não está autorizada.')
            db.execute('DELETE FROM sessions WHERE expires_at <= ?', (time.time(),))
            db.execute('INSERT INTO sessions VALUES (?, ?, ?)', (hashlib.sha256(token.encode()).hexdigest(), user_id, time.time() + SESSION_SECONDS))
        return token

    def current_user(self, token: str):
        with self.connection() as db:
            row = db.execute('''SELECT u.id, u.name, u.email, a.role, a.state FROM sessions s
                JOIN users u ON u.id=s.user_id JOIN account_access a ON a.user_id=u.id
                WHERE a.state='active' AND s.token_hash=? AND s.expires_at>?''',
                (hashlib.sha256(token.encode()).hexdigest(), time.time())).fetchone()
        if not row:
            raise HTTPException(401, 'Entre na sua conta para continuar.', headers={'WWW-Authenticate': 'Bearer'})
        return dict(row)

    def revoke(self, token: str):
        with self.connection() as db:
            db.execute('DELETE FROM sessions WHERE token_hash=?', (hashlib.sha256(token.encode()).hexdigest(),))

    def _user(self, db, user_id):
        row = db.execute('''SELECT u.id, u.name, u.email,
            COALESCE(a.role, 'user') AS role, COALESCE(a.state, 'pending') AS state
            FROM users u LEFT JOIN account_access a ON a.user_id=u.id WHERE u.id=?''',
            (user_id,)).fetchone()
        return dict(row) if row else None

    def bootstrap_admin(self, email: str, password: str):
        """Somente CLI local: prova a senha da conta existente e instala o primeiro administrador."""
        with self.connection() as db:
            row = db.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
        valid = password_hash.verify(password, row['password_hash'] if row else _dummy_hash)
        if not row or not valid:
            raise HTTPException(401, 'E-mail ou senha incorretos.')
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            admin = db.execute("SELECT user_id FROM account_access WHERE role='admin'", ()).fetchone()
            if admin and admin['user_id'] != row['id']:
                raise ValueError('Já existe um administrador. Operação cancelada.')
            db.execute('''INSERT INTO account_access VALUES (?, 'active', 'admin')
                ON CONFLICT(user_id) DO UPDATE SET state='active', role='admin' ''', (row['id'],))
            db.execute('DELETE FROM sessions WHERE user_id=?', (row['id'],))
            return self._user(db, row['id'])

    def _require_admin(self, db, actor_id):
        actor = self._user(db, actor_id)
        if not actor or actor['role'] != 'admin' or actor['state'] != 'active':
            raise HTTPException(403, 'Acesso exclusivo do administrador.')

    def list_accounts(self, actor_id):
        with self.connection() as db:
            self._require_admin(db, actor_id)
            rows = db.execute('''SELECT u.id, u.name, u.email,
                COALESCE(a.role, 'user') AS role, COALESCE(a.state, 'pending') AS state
                FROM users u LEFT JOIN account_access a ON a.user_id=u.id ORDER BY u.email''').fetchall()
        return [dict(row) for row in rows]

    def change_access(self, actor_id, target_id, action):
        transitions = {'authorize': ('pending', 'active'), 'block': ('active', 'blocked'), 'reactivate': ('blocked', 'active')}
        if action not in transitions:
            raise HTTPException(422, 'Ação inválida.')
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            self._require_admin(db, actor_id)
            target = self._user(db, target_id)
            if not target:
                raise HTTPException(404, 'Conta não encontrada.')
            if target['role'] == 'admin' or target_id == actor_id:
                raise HTTPException(403, 'A conta do administrador está protegida.')
            before, after = transitions[action]
            if target['state'] != before:
                raise HTTPException(409, 'O estado da conta mudou. Atualize a lista.')
            db.execute('''INSERT INTO account_access VALUES (?, ?, 'user')
                ON CONFLICT(user_id) DO UPDATE SET state=excluded.state''', (target_id, after))
            db.execute('DELETE FROM sessions WHERE user_id=?', (target_id,))
            db.execute('INSERT INTO admin_audit VALUES (?, ?, ?, ?, ?)', (str(uuid4()), actor_id, target_id, action, time.time()))
            return self._user(db, target_id)

    def delete_account(self, actor_id, target_id, confirmation_email):
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            self._require_admin(db, actor_id)
            target = self._user(db, target_id)
            if not target:
                raise HTTPException(404, 'Conta não encontrada.')
            if target['role'] == 'admin' or target_id == actor_id:
                raise HTTPException(403, 'A conta do administrador está protegida.')
            if confirmation_email.strip().casefold() != target['email']:
                raise HTTPException(422, 'Digite o e-mail da conta para confirmar a exclusão.')
            for table in ('sessions', 'profiles', 'private_applications', 'account_access'):
                db.execute(f'DELETE FROM {table} WHERE user_id=?', (target_id,))
            db.execute('DELETE FROM users WHERE id=?', (target_id,))
            db.execute('INSERT INTO admin_audit VALUES (?, ?, ?, ?, ?)', (str(uuid4()), actor_id, target_id, 'delete', time.time()))
        return {'deleted': True, 'user_id': target_id}


def get_store() -> AccountStore:
    url = os.getenv('ACCOUNT_DATABASE_URL', '').strip()
    if url:
        return _postgres_store(url)
    return AccountStore(os.getenv('ACCOUNT_DATABASE_PATH', 'data/private/accounts.sqlite3'))


class _AccountRow(dict):
    """Compatibilidade com os acessos por nome e índice usados no SQLite."""

    def __getitem__(self, key):
        if isinstance(key, int):
            return tuple(self.values())[key]
        return super().__getitem__(key)


def _account_row_factory(cursor):
    names = [column.name for column in cursor.description] if cursor.description else []
    return lambda values: _AccountRow(zip(names, values))


class _PostgresConnection:
    def __init__(self, connection):
        self.connection = connection

    def execute(self, query, parameters=None):
        if query.strip().upper() == 'BEGIN IMMEDIATE':
            # Transacional e compatível com o pool do Neon. Serializa limites/importações.
            return self.connection.execute('SELECT pg_advisory_xact_lock(7347844601)')
        # Apenas SQL interno parametrizado: nenhum valor é interpolado no texto.
        if parameters is not None:
            query = query.replace('%', '%%').replace('?', '%s')
        return self.connection.execute(query, parameters)


class PostgresAccountStore(AccountStore):
    def __init__(self, url: str):
        if not url.startswith(('postgresql://', 'postgres://')):
            raise ValueError('ACCOUNT_DATABASE_URL precisa ser uma conexão Postgres.')
        try:
            options = psycopg.conninfo.conninfo_to_dict(url)
        except psycopg.Error:
            raise ValueError('Conexão Postgres inválida. Confira a configuração.') from None
        if options.get('sslmode') not in (None, 'require', 'verify-ca', 'verify-full'):
            raise ValueError('A conexão Postgres precisa usar SSL.')
        options.setdefault('sslmode', 'require')
        self._options = options
        with self.connection() as db:
            db.execute('SELECT pg_advisory_xact_lock(7347844602)')
            for statement in (
                'CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL, name TEXT NOT NULL, password_hash TEXT NOT NULL)',
                'CREATE TABLE IF NOT EXISTS sessions (token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id), expires_at DOUBLE PRECISION NOT NULL)',
                'CREATE TABLE IF NOT EXISTS profiles (user_id TEXT PRIMARY KEY REFERENCES users(id), payload TEXT NOT NULL)',
                'CREATE TABLE IF NOT EXISTS private_applications (user_id TEXT NOT NULL REFERENCES users(id), application_id TEXT NOT NULL, payload TEXT NOT NULL, PRIMARY KEY(user_id, application_id))',
                'CREATE TABLE IF NOT EXISTS attempts (bucket TEXT NOT NULL, occurred_at DOUBLE PRECISION NOT NULL)',
                'CREATE INDEX IF NOT EXISTS attempts_bucket ON attempts(bucket, occurred_at)',
                "CREATE TABLE IF NOT EXISTS account_access (user_id TEXT PRIMARY KEY REFERENCES users(id), state TEXT NOT NULL CHECK(state IN ('pending', 'active', 'blocked')), role TEXT NOT NULL CHECK(role IN ('user', 'admin')))",
                'CREATE TABLE IF NOT EXISTS admin_audit (id TEXT PRIMARY KEY, actor_id TEXT NOT NULL, target_id TEXT NOT NULL, action TEXT NOT NULL, occurred_at DOUBLE PRECISION NOT NULL)',
            ):
                db.execute(statement)

    @contextmanager
    def connection(self):
        try:
            with psycopg.connect(**self._options, connect_timeout=15,
                                 row_factory=_account_row_factory, prepare_threshold=None) as db:
                yield _PostgresConnection(db)
        except psycopg.OperationalError:
            raise RuntimeError('Não foi possível conectar ao banco de contas. Confira a configuração do servidor.') from None


@lru_cache(maxsize=4)
def _postgres_store(url: str) -> PostgresAccountStore:
    return PostgresAccountStore(url)


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
