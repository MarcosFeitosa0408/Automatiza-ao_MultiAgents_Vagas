"""Pix da conta autenticada. Valores e confirmacao controlados pelo servidor."""
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, SecretStr, field_validator

from core.accounts import get_store
from core.auth_api import require_user
from core.pagbank import PagBankClient, PixExpirationRejected
from core.payment_store import PaymentStore
from core.subscriptions import SubscriptionStore

router = APIRouter(prefix="/pix", tags=["Pagamento"])


class PixRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tax_id: SecretStr

    @field_validator("tax_id")
    @classmethod
    def validate_cpf(cls, value):
        cpf = value.get_secret_value()
        if not cpf.isascii() or not cpf.isdigit() or len(cpf) != 11:
            raise ValueError("Informe seu CPF com onze digitos, sem pontuacao.")
        if len(set(cpf)) == 1:
            raise ValueError("CPF invalido.")
        for length in (9, 10):
            total = sum(int(cpf[i]) * (length + 1 - i) for i in range(length))
            digit = (total * 10) % 11
            if digit == 10:
                digit = 0
            if digit != int(cpf[length]):
                raise ValueError("CPF invalido.")
        return value


def public_payment(payment):
    return {
        key: payment[key]
        for key in (
            "id", "amount", "state", "environment", "qr_text",
            "period_start", "period_end",
        )
    }


def frozen_request(store, payment, user, tax_id):
    # Guarda a mesma requisicao em armazenamento privado para repetir com
    # idempotencia caso a rede falhe. Nunca retorna CPF para a interface.
    with store.connection() as db:
        db.execute("BEGIN IMMEDIATE")
        db.execute("""
            CREATE TABLE IF NOT EXISTS subscription_payment_requests (
                payment_id TEXT PRIMARY KEY
                    REFERENCES subscription_payments(id) ON DELETE CASCADE,
                payload TEXT NOT NULL
            )
        """)
        row = db.execute(
            "SELECT payload FROM subscription_payment_requests WHERE payment_id=?",
            (payment["id"],),
        ).fetchone()
        if row:
            return json.loads(row["payload"])

        parameters = {
            "reference": payment["reference"],
            "name": user["name"],
            "email": user["email"],
            "tax_id": tax_id,
            "amount": payment["amount"],
            "expires_at": datetime.fromtimestamp(
                payment["created_at"] + 1800, timezone.utc
            ).isoformat(timespec="seconds"),
        }
        db.execute(
            "INSERT INTO subscription_payment_requests VALUES (?, ?)",
            (payment["id"], json.dumps(parameters)),
        )
        return parameters


@router.post("")
def create_pix(payload: PixRequest, user=Depends(require_user)):
    store = get_store()
    store.limit("pix-create:" + user["id"], 15)
    client = PagBankClient()
    SubscriptionStore(store)
    payments = PaymentStore(store)
    for attempt in range(2):
        payment = payments.reserve(user["id"], client.environment)

        # Confira a cobranca anterior antes de oferecer outro QR Code.
        # Se ja estiver paga, devolva a confirmacao, sem cobrar novamente.
        if payment["state"] == "WAITING" and payment["order_id"]:
            payment = payments.confirm(payment["id"], user["id"], client)
            if payment["state"] in ("EXPIRED", "DECLINED", "CANCELED"):
                payment = payments.reserve(user["id"], client.environment)

        if payment["state"] == "CREATING":
            parameters = frozen_request(
                store, payment, user, payload.tax_id.get_secret_value()
            )
            try:
                order = client.create_pix(**parameters)
            except PixExpirationRejected:
                if attempt == 1:
                    raise
                replaced = payments.expire_rejected_creation(
                    payment["id"], user["id"]
                )
                if not replaced:
                    raise
                continue
            payment = payments.record_order(payment["id"], user["id"], order)
            # Depois de registrar o pedido, a requisicao com CPF nao e mais
            # necessaria para recuperar o pagamento.
            with store.connection() as db:
                db.execute(
                    "DELETE FROM subscription_payment_requests WHERE payment_id=?",
                    (payment["id"],),
                )
        return public_payment(payment)


@router.get("/{payment_id}")
def check_pix(payment_id: str, user=Depends(require_user)):
    store = get_store()
    store.limit("pix-check:" + user["id"], 120)
    client = PagBankClient()
    SubscriptionStore(store)
    payments = PaymentStore(store)
    payment = payments.get(payment_id, user["id"])
    if payment["environment"] != client.environment:
        raise HTTPException(404, "Pagamento nao encontrado neste ambiente.")
    if payment["order_id"]:
        payment = payments.confirm(payment_id, user["id"], client)
    return public_payment(payment)
