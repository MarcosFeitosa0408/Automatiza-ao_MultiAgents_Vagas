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
