"""Controle de acesso exclusivo do administrador; não expõe perfis ou senhas."""
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from core.accounts import get_store
from core.auth_api import require_user

router = APIRouter(prefix='/admin', tags=['Administração'])


def require_admin(user=Depends(require_user)):
    if user['role'] != 'admin':
        raise HTTPException(403, 'Acesso exclusivo do administrador.')
    return user


class AccessRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    action: Literal['authorize', 'block', 'reactivate']


class DeleteAccountRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    confirmation_email: str = Field(min_length=3, max_length=254)


@router.get('/users')
def list_users(admin=Depends(require_admin)):
    return get_store().list_accounts(admin['id'])


@router.patch('/users/{user_id}/access')
def change_access(user_id: str, payload: AccessRequest, admin=Depends(require_admin)):
    return get_store().change_access(admin['id'], user_id, payload.action)


@router.delete('/users/{user_id}')
def delete_account(user_id: str, payload: DeleteAccountRequest, admin=Depends(require_admin)):
    return get_store().delete_account(admin['id'], user_id, payload.confirmation_email)

@router.get('/members')
def list_members(admin=Depends(require_admin)):
    from core.subscriptions import SubscriptionStore

    store = get_store()
    accounts = store.list_accounts(admin['id'])
    subscriptions = SubscriptionStore(store)
    from core.access_history import ensure_access_history
    with store.connection() as db:
        ensure_access_history(db)
    members = []

    for account in accounts:
        with store.connection() as db:
            entries = db.execute(
                "SELECT event, occurred_at FROM account_entry_history "
                "WHERE user_id=? ORDER BY occurred_at DESC, id DESC",
                (account['id'],),
            ).fetchall()
            payments = db.execute(
                "SELECT id, amount, state, environment, created_at, "
                "period_start, period_end FROM subscription_payments "
                "WHERE user_id=? ORDER BY created_at DESC",
                (account['id'],),
            ).fetchall()

        members.append({
            'id': account['id'],
            'name': account['name'],
            'email': account['email'],
            'role': account['role'],
            'state': account['state'],
            'subscription': subscriptions.status(account['id']),
            'payments': [dict(payment) for payment in payments],
            'access_history': [dict(entry) for entry in entries],
        })

    return {'members': members}
