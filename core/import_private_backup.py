"""Importa um backup local para uma conta já cadastrada, sem expor senha."""
import argparse
import getpass
import json
from pathlib import Path

from core.accounts import empty_profile, get_store
from core.schemas.candidate import MasterProfile
from core.schemas.job_application import JobApplicationObject


def import_backup(store, user, folder):
    folder = Path(folder)
    profile = MasterProfile.model_validate_json((folder / 'MASTER_PROFILE.json').read_text(encoding='utf-8-sig'))
    raw = json.loads((folder / 'job-applications.json').read_text(encoding='utf-8-sig'))
    if isinstance(raw, dict):
        raw = [raw]
    if not isinstance(raw, list):
        raise ValueError('O backup de candidaturas precisa conter uma lista.')
    applications = [JobApplicationObject.model_validate(item) for item in raw]
    if len({item.application_id for item in applications}) != len(applications):
        raise ValueError('O backup contém IDs repetidos.')
    profile = profile.model_copy(update={'candidate_id': user['id']})
    initial = empty_profile(user['id'], user['name'], user['email'])
    with store.connection() as db:
        db.execute('BEGIN IMMEDIATE')
        row = db.execute('SELECT payload FROM profiles WHERE user_id=?', (user['id'],)).fetchone()
        current = MasterProfile.model_validate_json(row['payload']) if row else None
        count = db.execute('SELECT COUNT(*) FROM private_applications WHERE user_id=?', (user['id'],)).fetchone()[0]
        if current != initial or count:
            raise ValueError('A conta já possui dados. Importação cancelada para preservar o conteúdo atual.')
        db.execute('UPDATE profiles SET payload=? WHERE user_id=?', (profile.model_dump_json(), user['id']))
        for item in applications:
            db.execute('INSERT INTO private_applications VALUES (?, ?, ?)', (user['id'], item.application_id, item.model_dump_json()))
    return len(applications)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backup', required=True, help='Pasta com MASTER_PROFILE.json e job-applications.json')
    parser.add_argument('--email', required=True, help='E-mail da sua conta cadastrada na plataforma')
    args = parser.parse_args()
    try:
        store = get_store()
        user = store.check_password(args.email.strip().casefold(), getpass.getpass('Senha da sua conta: '))
        count = import_backup(store, user, args.backup)
        print(f'Importação concluída: perfil e {count} candidatura(s). Entre novamente na plataforma.')
    except Exception as error:
        from fastapi import HTTPException
        if isinstance(error, HTTPException):
            print('Importação cancelada: e-mail ou senha incorretos.')
        elif isinstance(error, ValueError):
            print('Importação cancelada. Confira o formato do backup e se a conta ainda está vazia.')
        else:
            print('Importação cancelada. Confira o caminho e os arquivos do backup.')
        raise SystemExit(1) from None


if __name__ == '__main__':
    main()
