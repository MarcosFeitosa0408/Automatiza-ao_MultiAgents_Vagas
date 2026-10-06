import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient
import main
from core.accounts import AccountStore
from core.auth_api import RegisterRequest, LoginRequest, ResetPasswordRequest
from core.password_recovery import reset_password
import hashlib, time


@pytest.mark.parametrize('model,extra', [(RegisterRequest,{'name':'Pessoa'}), (LoginRequest,{}), (ResetPasswordRequest,{'token':'a'*64})])
def test_minimum_eight_characters(model, extra):
    base = {'email':'test@example.invalid'} if model is not ResetPasswordRequest else {}
    assert model.model_validate({**base, **extra, 'password':'Abc12345'})
    with pytest.raises(ValidationError):
        model.model_validate({**base, **extra, 'password':'Abc1234'})
    with pytest.raises(ValidationError):
        model.model_validate({**base, **extra, 'password':'a'*129})


def test_eight_character_account_and_reset_preserve_existing_accounts(tmp_path, monkeypatch):
    store=AccountStore(str(tmp_path/'accounts.sqlite3'))
    monkeypatch.setattr('core.auth_api.get_store', lambda: store)
    old=store.create_user('Anterior','old@example.invalid','Senha anterior longa!')
    store.bootstrap_admin(old['email'],'Senha anterior longa!')
    with TestClient(main.app) as client:
        assert client.post('/auth/register',json={'name':'Nova','email':'new@example.invalid','password':'Abc12345'}).status_code==201
        with store.connection() as db:
            new_id=db.execute('SELECT id FROM users WHERE email=?',('new@example.invalid',)).fetchone()['id']
        store.change_access(old['id'],new_id,'authorize')
        assert client.post('/auth/login',json={'email':'new@example.invalid','password':'Abc12345'}).status_code==200
        assert client.post('/auth/login',json={'email':old['email'],'password':'Senha anterior longa!'}).status_code==200
        token='test-token-reset-eight-characters'
        with store.connection() as db:
            db.execute('INSERT INTO password_resets VALUES (?, ?, ?)',(hashlib.sha256(token.encode()).hexdigest(),new_id,time.time()+60))
        assert reset_password(store,token,'Nova1234')['message']
        assert client.post('/auth/login',json={'email':'new@example.invalid','password':'Nova1234'}).status_code==200
