"""Configura o primeiro administrador usando uma conta existente e sua senha."""
import argparse
import getpass
from core.accounts import get_store, PostgresAccountStore


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--email', required=True)
    args = parser.parse_args()
    try:
        store = get_store()
        print('Banco selecionado:', 'Postgres' if isinstance(store, PostgresAccountStore) else 'SQLite local')
        store.bootstrap_admin(args.email.strip().casefold(), getpass.getpass('Senha da sua conta na plataforma: '))
    except Exception:
        print('Configuração cancelada. Confira a conta, a senha, o banco configurado e se já existe outro administrador.')
        raise SystemExit(1) from None
    print('Conta de administrador configurada. Seus perfis e vagas foram preservados.')
    print('Entre novamente para acessar Administrar acessos.')


if __name__ == '__main__':
    main()
