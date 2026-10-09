from copy import deepcopy

import pytest
from fastapi import HTTPException

from core.pagbank import PagBankClient, payment_is_confirmed


def paid_order():
    return {
        "id": "ORDE_test-001",
        "reference_id": "payment-test-001",
        "charges": [{
            "reference_id": "payment-test-001",
            "status": "PAID",
            "payment_method": {"type": "PIX"},
            "amount": {
                "value": 1990,
                "currency": "BRL",
                "summary": {"paid": 1990, "refunded": 0},
            },
        }],
    }


def confirmed(order):
    return payment_is_confirmed(
        order,
        order_id="ORDE_test-001",
        reference="payment-test-001",
        amount=1990,
    )


def test_accepts_only_confirmed_pix_for_expected_order():
    assert confirmed(paid_order()) is True


@pytest.mark.parametrize("case", [
    "other_order", "other_reference", "other_charge_reference",
    "waiting", "wrong_amount", "wrong_currency",
    "partial_payment", "refunded", "other_method", "multiple_charges",
])
def test_rejects_payment_that_does_not_match(case):
    order = deepcopy(paid_order())
    charge = order["charges"][0]
    if case == "other_order":
        order["id"] = "ORDE_other"
    elif case == "other_reference":
        order["reference_id"] = "other"
    elif case == "other_charge_reference":
        charge["reference_id"] = "other"
    elif case == "waiting":
        charge["status"] = "WAITING"
    elif case == "wrong_amount":
        charge["amount"]["value"] = 2990
    elif case == "wrong_currency":
        charge["amount"]["currency"] = "USD"
    elif case == "partial_payment":
        charge["amount"]["summary"]["paid"] = 100
    elif case == "refunded":
        charge["amount"]["summary"]["refunded"] = 1990
    elif case == "other_method":
        charge["payment_method"]["type"] = "CREDIT_CARD"
    elif case == "multiple_charges":
        order["charges"].append(deepcopy(charge))
    assert confirmed(order) is False


def test_production_requires_explicit_enablement(monkeypatch):
    monkeypatch.setenv("PAGBANK_ENVIRONMENT", "production")
    monkeypatch.setenv("PAGBANK_TOKEN", "fake-token-only-for-tests")
    monkeypatch.delenv("PAGBANK_PRODUCTION_ENABLED", raising=False)
    with pytest.raises(HTTPException) as error:
        PagBankClient()
    assert error.value.status_code == 503


def test_missing_token_does_not_allow_payments(monkeypatch):
    monkeypatch.setenv("PAGBANK_ENVIRONMENT", "sandbox")
    monkeypatch.delenv("PAGBANK_TOKEN", raising=False)
    with pytest.raises(HTTPException) as error:
        PagBankClient()
    assert error.value.status_code == 503


def test_pix_uses_server_amount_and_same_idempotency_key(monkeypatch):
    monkeypatch.setenv("PAGBANK_ENVIRONMENT", "sandbox")
    monkeypatch.setenv("PAGBANK_TOKEN", "fake-token-only-for-tests")
    client = PagBankClient()
    calls = []

    def capture(path, *, payload=None, reference=None):
        calls.append((path, payload, reference))
        return {"id": "ORDE_test"}

    monkeypatch.setattr(client, "_request", capture)
    client.create_pix(
        reference="payment-test-001",
        name="Candidato de Teste",
        email="candidate@example.invalid",
        tax_id="12345678909",
        amount=1990,
    )
    path, payload, reference = calls[0]
    assert path == "/orders"
    assert reference == payload["reference_id"]
    assert payload["charges"][0]["reference_id"] == reference
    assert payload["charges"][0]["amount"] == {
        "value": 1990, "currency": "BRL",
    }

    with pytest.raises(ValueError):
        client.create_pix(
            reference="payment-test-002",
            name="Teste",
            email="candidate@example.invalid",
            tax_id="12345678909",
            amount=1,
        )
    assert len(calls) == 1
