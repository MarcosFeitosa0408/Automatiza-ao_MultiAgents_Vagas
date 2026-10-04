"""Confere o banco de contas sem mostrar conexão, senhas ou dados pessoais."""
import os
from core.accounts import get_store, PostgresAccountStore


def main():
    if not os.getenv('ACCOUNT_DATABASE_URL', '').strip():
        print('Teste cancelado: configure ACCOUNT_DATABASE_URL neste terminal.')
        raise SystemExit(1)
    try:
        store = get_store()
        if not isinstance(store, PostgresAccountStore):
            raise ValueError('Banco incorreto.')
        with store.connection() as db:
            db.execute('SELECT 1 FROM users LIMIT 1').fetchone()
            db.execute('SELECT 1 FROM profiles LIMIT 1').fetchone()
            db.execute('SELECT 1 FROM private_applications LIMIT 1').fetchone()
        print('Conexão Postgres confirmada. Tabelas de contas prontas.')
        print('Nenhuma conta ou perfil local foi transferido por este teste.')
    except Exception:
        print('Falha ao verificar o Postgres. Confira a conexão completa, a senha e a rede. Não envie a conexão no chat.')
        raise SystemExit(1) from None


if __name__ == '__main__':
    main()
