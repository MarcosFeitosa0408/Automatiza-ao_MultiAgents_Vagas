"""Comunicacao com PagBank. Credenciais ficam somente no servidor."""
import json
import logging
import os
import re
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError, URLError
from urllib.request import (
    HTTPRedirectHandler, Request, build_opener,
)

from fastapi import HTTPException



class PixExpirationRejected(HTTPException):
    def __init__(self):
        super().__init__(
            502,
            "O PagBank rejeitou a data de vencimento desta solicitacao.",
        )


def pix_expiration_was_rejected(error):
    if not isinstance(error, HTTPError) or error.code != 400:
        return False
    try:
        body = error.read(65537)
        if len(body) > 65536:
            return False
        result = json.loads(body)
    except (ValueError, UnicodeError, OSError):
        return False
    if not isinstance(result, dict):
        return False
    messages = result.get("error_messages")
    if not isinstance(messages, list) or len(messages) != 1:
        return False
    message = messages[0]
    return (
        isinstance(message, dict)
        and message.get("code") == "40002"
        and message.get("parameter_name")
        == "charges[0].payment_method.pix.expiration_date"
        and message.get("description") == "must be a future date"
    )


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class PagBankClient:
    def __init__(self):
        environment = os.getenv("PAGBANK_ENVIRONMENT", "").strip()
        self.token = os.getenv("PAGBANK_TOKEN", "").strip()
        if environment not in ("sandbox", "production") or not self.token:
            raise HTTPException(503, "Pagamento por Pix indisponivel no momento.")
        if environment == "production" and os.getenv(
            "PAGBANK_PRODUCTION_ENABLED", ""
        ).lower() != "true":
            raise HTTPException(503, "Pagamento real ainda nao habilitado.")
        self.environment = environment
        self.base_url = (
            "https://sandbox.api.pagseguro.com"
            if environment == "sandbox"
            else "https://api.pagseguro.com"
        )

    def _request(self, path, *, payload=None, reference=None):
        headers = {
            "Authorization": "Bearer " + self.token,
            "Accept": "application/json",
            "User-Agent": "MultiAgentsVagas-SandboxTest/1.0",
        }
        data = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            headers["x-idempotency-key"] = reference
            data = json.dumps(payload).encode("utf-8")

        request = Request(
            self.base_url + path,
            data=data,
            headers=headers,
            method="POST" if data is not None else "GET",
        )
        try:
            with build_opener(NoRedirect()).open(
                request, timeout=30
            ) as response:
                body = response.read(1024 * 1024 + 1)
                if len(body) > 1024 * 1024:
                    raise ValueError("Resposta muito grande")
                result = json.loads(body)
                if not isinstance(result, dict):
                    raise ValueError("Resposta inesperada")
                return result
        except (HTTPError, URLError, TimeoutError, OSError,
                ValueError, UnicodeError) as error:
            logging.getLogger(__name__).warning(
                "PagBank: falha na requisicao; tipo=%s; HTTP=%s",
                type(error).__name__,
                error.code if isinstance(error, HTTPError) else "nao informado",
            )
            # Somente a rejeicao explicita permite substituir a solicitacao.
            if pix_expiration_was_rejected(error):
                raise PixExpirationRejected() from None
            # Nao expoe token, dados pessoais ou resposta bruta do banco.
            raise HTTPException(
                502,
                "Nao foi possivel confirmar a operacao com o PagBank. "
                "Nenhum acesso foi liberado por esta resposta.",
            ) from None

    def create_pix(self, *, reference, name, email, tax_id, amount, expires_at=None):
        if amount not in (1990, 2990):
            raise ValueError("Valor de mensalidade invalido.")
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", reference):
            raise ValueError("Referencia invalida.")
        if not re.fullmatch(r"\d{11}", tax_id):
            raise ValueError("CPF precisa conter onze digitos.")

        expiration = expires_at or (
            datetime.now(timezone.utc) + timedelta(minutes=30)
        ).isoformat(timespec="seconds")
        return self._request(
            "/orders",
            reference=reference,
            payload={
                "reference_id": reference,
                "customer": {
                    "name": name,
                    "email": email,
                    "tax_id": tax_id,
                },
                "items": [{
                    "name": "MultiAgents Vagas - acesso mensal",
                    "quantity": 1,
                    "unit_amount": amount,
                }],
                "charges": [{
                    "reference_id": reference,
                    "description": "MultiAgents Vagas - acesso mensal",
                    "amount": {"value": amount, "currency": "BRL"},
                    "payment_method": {
                        "type": "PIX",
                        "pix": {"expiration_date": expiration},
                    },
                }],
            },
        )

    def consult_order(self, order_id):
        if not re.fullmatch(r"ORDE_[A-Za-z0-9-]{1,80}", order_id):
            raise ValueError("Identificador de pedido invalido.")
        return self._request("/orders/" + order_id)


def payment_is_confirmed(order, *, order_id, reference, amount):
    """Usar somente com resposta consultada pelo servidor no PagBank."""
    if amount not in (1990, 2990) or not isinstance(order, dict):
        return False
    if order.get("id") != order_id or order.get("reference_id") != reference:
        return False

    charges = order.get("charges")
    if not isinstance(charges, list) or len(charges) != 1:
        return False
    charge = charges[0]
    if not isinstance(charge, dict):
        return False

    values = charge.get("amount") or {}
    if not isinstance(values, dict):
        return False
    summary = values.get("summary") or {}
    if not isinstance(summary, dict):
        return False
    method = charge.get("payment_method") or {}
    if not isinstance(method, dict):
        return False

    return (
        charge.get("reference_id") == reference
        and charge.get("status") == "PAID"
        and method.get("type") == "PIX"
        and values.get("currency") == "BRL"
        and values.get("value") == amount
        and summary.get("paid") == amount
        and summary.get("refunded") == 0
    )
