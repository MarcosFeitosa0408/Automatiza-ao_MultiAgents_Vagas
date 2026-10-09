import pytest
from fastapi.testclient import TestClient

import main
from core import auth_api, payment_api
from core.accounts import AccountStore
from core.subscriptions import SubscriptionStore


class FakeBank:
    environment = "sandbox"

    def __init__(self):
        self.orders = {}
        self.calls = 0

    def create_pix(self, **parameters):
        self.calls += 1
        reference = parameters["reference"]
        order = {
            "id": "ORDE_" + reference,
            "reference_id": reference,
            "charges": [{
                "reference_id": reference,
                "status": "WAITING",
                "payment_method": {"type": "PIX"},
                "amount": {
                    "value": parameters["amount"],
                    "currency": "BRL",
                    "summary": {"paid": 0, "refunded": 0},
                },
                "qr_code": {"text": "codigo-apenas-para-teste"},
            }],
        }
        self.orders[order["id"]] = order
        return order

    def consult_order(self, order_id):
        return self.orders[order_id]


@pytest.fixture
def pix_case(tmp_path, monkeypatch):
    monkeypatch.setenv("PAGBANK_ENVIRONMENT", "sandbox")
    store = AccountStore(str(tmp_path / "accounts.sqlite3"))
    admin = store.create_user("Admin", "admin@example.invalid", "SenhaTeste123!")
    store.bootstrap_admin(admin["email"], "SenhaTeste123!")
    subscriptions = SubscriptionStore(store)
    headers = []
    for index in range(2):
        user = store.create_user(
            "Teste", f"user{index}@example.invalid", "SenhaTeste123!"
        )
        store.change_access(admin["id"], user["id"], "authorize")
        subscriptions.enroll(user["id"])
        headers.append({
            "Authorization": "Bearer " + store.issue_session(user["id"]),
        })
    bank = FakeBank()
    monkeypatch.setattr(auth_api, "get_store", lambda: store)
    monkeypatch.setattr(payment_api, "get_store", lambda: store)
    monkeypatch.setattr(payment_api, "PagBankClient", lambda: bank)
    with TestClient(main.app) as client:
        yield client, headers, bank


def test_pix_requires_login(pix_case):
    client, _, _ = pix_case
    assert client.post("/auth/pix", json={"tax_id": "12345678909"}).status_code == 401
    assert client.get("/auth/pix/unknown").status_code == 401


def test_candidate_cannot_choose_price(pix_case):
    client, headers, bank = pix_case
    response = client.post("/auth/pix", headers=headers[0], json={
        "tax_id": "12345678909", "amount": 1,
    })
    assert response.status_code == 422
    assert bank.calls == 0


def test_pix_reuses_charge_is_private_and_confirms_payment(pix_case):
    client, headers, bank = pix_case
    first = client.post(
        "/auth/pix", headers=headers[0], json={"tax_id": "12345678909"}
    )
    assert first.status_code == 200
    payment = first.json()
    assert payment["amount"] == 1990
    assert payment["state"] == "WAITING"
    assert "tax_id" not in payment
    assert "payload" not in payment

    repeated = client.post(
        "/auth/pix", headers=headers[0], json={"tax_id": "12345678909"}
    )
    assert repeated.json()["id"] == payment["id"]
    assert bank.calls == 1

    url = "/auth/pix/" + payment["id"]
    assert client.get(url, headers=headers[1]).status_code == 404
    assert client.get(url, headers=headers[0]).json()["state"] == "WAITING"

    order = next(iter(bank.orders.values()))
    order["charges"][0]["status"] = "PAID"
    order["charges"][0]["amount"]["summary"]["paid"] = 1990
    confirmed = client.get(url, headers=headers[0])
    assert confirmed.status_code == 200
    assert confirmed.json()["state"] == "PAID"
    assert confirmed.json()["period_end"] > confirmed.json()["period_start"]
    again = client.get(url, headers=headers[0])
    assert again.json()["period_end"] == confirmed.json()["period_end"]


def test_invalid_cpf_does_not_create_payment(pix_case):
    client, headers, bank = pix_case
    response = client.post(
        "/auth/pix", headers=headers[0], json={"tax_id": "11111111111"}
    )
    assert response.status_code == 422
    assert bank.calls == 0



def test_pix_api_replaces_expired_charge_without_losing_history(pix_case):
    import time

    client, headers, bank = pix_case
    first = client.post(
        "/auth/pix", headers=headers[0], json={"tax_id": "12345678909"}
    )
    assert first.status_code == 200
    old_id = first.json()["id"]

    with auth_api.get_store().connection() as db:
        db.execute(
            "UPDATE subscription_payments SET created_at=? WHERE id=?",
            (time.time() - 1801, old_id),
        )

    replacement = client.post(
        "/auth/pix", headers=headers[0], json={"tax_id": "12345678909"}
    )
    assert replacement.status_code == 200
    assert replacement.json()["id"] != old_id
    assert replacement.json()["amount"] == 1990
    assert bank.calls == 2

    with auth_api.get_store().connection() as db:
        old = db.execute(
            "SELECT state, qr_text FROM subscription_payments WHERE id=?",
            (old_id,),
        ).fetchone()
    assert old["state"] == "EXPIRED"
    assert old["qr_text"] is None


def test_pix_recovers_explicitly_rejected_expiration(pix_case, monkeypatch):
    import time
    from datetime import datetime
    from core.pagbank import PixExpirationRejected
    from core.payment_store import PaymentStore

    client, headers, bank = pix_case
    store = payment_api.get_store()
    token = headers[0]["Authorization"].removeprefix("Bearer ")
    user = store.current_user(token)
    payments = PaymentStore(store)
    old = payments.reserve(
        user["id"], "sandbox", now=time.time() - 3600
    )

    original_create = bank.create_pix
    attempts = []

    def create_with_expiration_check(**parameters):
        attempts.append(parameters)
        expires = datetime.fromisoformat(
            parameters["expires_at"]
        ).timestamp()
        if expires <= time.time():
            raise PixExpirationRejected()
        return original_create(**parameters)

    monkeypatch.setattr(bank, "create_pix", create_with_expiration_check)
    response = client.post(
        "/auth/pix",
        headers=headers[0],
        json={"tax_id": "12345678909"},
    )

    assert response.status_code == 200
    current = response.json()
    assert current["state"] == "WAITING"
    assert current["amount"] == 1990
    assert current["id"] != old["id"]
    assert len(attempts) == 2
    assert attempts[0]["reference"] != attempts[1]["reference"]
    assert payments.get(old["id"], user["id"])["state"] == "EXPIRED"

    repeated = client.post(
        "/auth/pix",
        headers=headers[0],
        json={"tax_id": "12345678909"},
    )
    assert repeated.json()["id"] == current["id"]
    assert len(attempts) == 2
