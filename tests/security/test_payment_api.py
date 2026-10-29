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



def test_pix_api_replaces_bank_canceled_charge_without_losing_history(pix_case):
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

    # So o prazo local nao permite substituicao enquanto o banco aguarda.
    waiting = client.post(
        "/auth/pix", headers=headers[0], json={"tax_id": "12345678909"}
    )
    assert waiting.json()["id"] == old_id
    assert waiting.json()["state"] == "WAITING"
    assert bank.calls == 1
    next(iter(bank.orders.values()))["charges"][0]["status"] = "CANCELED"

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
    assert old["state"] == "CANCELED"
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


@pytest.mark.parametrize("reverse", [False, True])
def test_legacy_expired_pix_and_replacement_paid_preserve_both_periods(
    pix_case, monkeypatch, reverse
):
    from types import SimpleNamespace
    from core import payment_store

    client, headers, bank = pix_case
    monkeypatch.setattr(payment_store, "time", SimpleNamespace(time=lambda: 1000))
    first = client.post(
        "/auth/pix", headers=headers[0], json={"tax_id": "12345678909"}
    ).json()
    store = payment_api.get_store()
    # Reproduz uma cobranca encerrada pelo comportamento anterior ao ajuste.
    with store.connection() as db:
        db.execute(
            "UPDATE subscription_payments SET state='EXPIRED', qr_text=NULL WHERE id=?",
            (first["id"],),
        )
    second = client.post(
        "/auth/pix", headers=headers[0], json={"tax_id": "12345678909"}
    ).json()
    assert first["id"] != second["id"]
    assert bank.calls == 2
    for order in bank.orders.values():
        charge = order["charges"][0]
        charge["status"] = "PAID"
        charge["amount"]["summary"]["paid"] = charge["amount"]["value"]

    ids = [first["id"], second["id"]]
    if reverse:
        ids.reverse()
    results = []
    for payment_id in ids:
        response = client.get("/auth/pix/" + payment_id, headers=headers[0])
        assert response.status_code == 200
        assert response.json()["state"] == "PAID"
        results.append(response.json())
    assert results[0]["period_start"] == 1000
    assert results[1]["period_start"] == results[0]["period_end"]
    assert results[1]["period_end"] == 1000 + 2 * payment_store.MONTH_SECONDS
    for result in results:
        again = client.get("/auth/pix/" + result["id"], headers=headers[0])
        assert again.json()["period_end"] == result["period_end"]
    user = store.current_user(headers[0]["Authorization"].removeprefix("Bearer "))
    status = SubscriptionStore(store).status(user["id"], now=1000)
    assert status["paid_ends_at"] == results[1]["period_end"]
    assert bank.calls == 2


def test_lost_creation_response_reuses_identical_request_after_deadline(
    pix_case, monkeypatch
):
    import io
    import json
    from types import SimpleNamespace
    from urllib.error import URLError
    from core import pagbank, payment_store

    client, headers, _ = pix_case
    monkeypatch.setenv("PAGBANK_TOKEN", "token-apenas-de-teste")
    monkeypatch.setattr(payment_api, "PagBankClient", pagbank.PagBankClient)
    clock = [1000]
    monkeypatch.setattr(payment_store, "time", SimpleNamespace(time=lambda: clock[0]))
    requests = []
    orders = {}

    class Response(io.BytesIO):
        status = 200

    class IdempotentBank:
        def open(self, request, timeout):
            if request.get_method() == "GET":
                order = next(iter(orders.values()))
                return Response(json.dumps(order).encode())
            key = request.get_header("X-idempotency-key")
            payload = json.loads(request.data)
            requests.append((key, request.data))
            if key not in orders:
                orders[key] = {
                    "id": "ORDE_" + key,
                    "reference_id": payload["reference_id"],
                    "charges": [{
                        **payload["charges"][0], "status": "WAITING",
                        "qr_code": {"text": "codigo-apenas-para-teste"},
                    }],
                }
                # O banco criou o pedido, mas o servidor perdeu a resposta.
                raise URLError("resposta perdida simulada")
            return Response(json.dumps(orders[key]).encode())

    monkeypatch.setattr(pagbank, "build_opener", lambda *args: IdempotentBank())
    failed = client.post(
        "/auth/pix", headers=headers[0], json={"tax_id": "12345678909"}
    )
    assert failed.status_code == 502
    store = payment_api.get_store()
    with store.connection() as db:
        original = dict(db.execute("SELECT * FROM subscription_payments").fetchone())
        assert original["state"] == "CREATING"
        # Mudancas no perfil nao podem modificar uma tentativa incerta.
        db.execute("UPDATE users SET name='Nome atualizado', email='updated@example.invalid' WHERE id=?", (original["user_id"],))
    assert SubscriptionStore(store).status(original["user_id"], now=1000)["access_allowed"] is False

    clock[0] = 2900
    recovered = client.post(
        "/auth/pix", headers=headers[0], json={"tax_id": "12345678909"}
    )
    assert recovered.status_code == 200
    assert recovered.json()["id"] == original["id"]
    assert recovered.json()["state"] == "WAITING"
    assert len(orders) == 1
    assert len(requests) == 2
    assert requests[0] == requests[1]
    assert requests[0][0] == original["reference"]
    with store.connection() as db:
        assert db.execute("SELECT COUNT(*) FROM subscription_payments").fetchone()[0] == 1
        assert db.execute("SELECT COUNT(*) FROM subscription_payment_requests").fetchone()[0] == 0

    charge = next(iter(orders.values()))["charges"][0]
    charge["status"] = "PAID"
    charge["amount"]["summary"] = {"paid": 1990, "refunded": 0}
    url = "/auth/pix/" + original["id"]
    confirmed = client.get(url, headers=headers[0])
    assert confirmed.json()["state"] == "PAID"
    assert confirmed.json()["period_end"] == 2900 + payment_store.MONTH_SECONDS
    assert client.get(url, headers=headers[0]).json()["period_end"] == confirmed.json()["period_end"]
    assert len(requests) == 2


def test_second_expiration_rejection_stops_recovery(pix_case, monkeypatch):
    from core.pagbank import PixExpirationRejected

    client, headers, bank = pix_case
    attempts = []

    def reject(**parameters):
        attempts.append(parameters)
        raise PixExpirationRejected()

    monkeypatch.setattr(bank, "create_pix", reject)
    response = client.post(
        "/auth/pix", headers=headers[0], json={"tax_id": "12345678909"}
    )
    assert response.status_code == 502
    assert len(attempts) == 2
    assert attempts[0]["reference"] != attempts[1]["reference"]
    store = payment_api.get_store()
    user = store.current_user(headers[0]["Authorization"].removeprefix("Bearer "))
    assert SubscriptionStore(store).status(user["id"])["access_allowed"] is False
    with payment_api.get_store().connection() as db:
        states = [row[0] for row in db.execute("SELECT state FROM subscription_payments").fetchall()]
    assert sorted(states) == ["CREATING", "EXPIRED"]
