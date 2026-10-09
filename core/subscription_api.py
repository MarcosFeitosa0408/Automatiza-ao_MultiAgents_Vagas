"""Consulta de acesso e ativação do teste da conta autenticada."""
from fastapi import APIRouter, Depends

from core.accounts import get_store
from core.auth_api import require_user
from core.subscriptions import SubscriptionStore


router = APIRouter(prefix="/auth", tags=["Assinatura"])


@router.get("/subscription")
def subscription_status(user=Depends(require_user)):
    return SubscriptionStore(get_store()).status(user["id"])


@router.post("/trial")
def activate_trial(user=Depends(require_user)):
    return SubscriptionStore(get_store()).start_trial(user["id"])


from core.payment_api import router as payment_router
router.include_router(payment_router)
