import pytest
from fastapi import HTTPException

from core.accounts import AccountStore
from core.payment_store import PaymentStore, MONTH_SECONDS
from core.subscriptions import SubscriptionStore


@pytest.fixture
def payment_case(tmp_path, monkeypatch):
    monkeypatch.setenv("PAGBANK_ENVIRONMENT", "sandbox")
    accounts = AccountStore(str(tmp_path / "accounts.sqlite3"))
    admin = accounts.create_user("Admin", "admin@example.invalid", "SenhaTeste123!")
    accounts.bootstrap_admin(admin["email"], "SenhaTeste123!")
    user = accounts.create_user("Teste", "user@example.invalid", "SenhaTeste123!")
    accounts.change_access(admin["id"], user["id"], "authorize")
    subscriptions = SubscriptionStore(accounts)
    subscriptions.enroll(user["id"])
    return accounts, subscriptions, PaymentStore(accounts), admin, user


def order_for(payment, status="PAID", amount=None):
    value = payment["amount"] if amount is None else amount
    return {
        "id": "ORDE_" + payment["id"],
        "reference_id": payment["reference"],
        "charges": [{
            "reference_id": payment["reference"],
            "status": status,
            "payment_method": {"type": "PIX"},
            "amount": {
                "value": value, "currency": "BRL",
                "summary": {"paid": value if status == "PAID" else 0, "refunded": 0},
            },
            "qr_code": {"text": "codigo-apenas-para-teste"},
        }],
    }


class FakeBank:
    environment = "sandbox"

    def __init__(self, order):
        self.order = order

    def consult_order(self, order_id):
        assert order_id == self.order["id"]
        return self.order


def test_confirmation_grants_thirty_days_only_once(payment_case):
    _, subscriptions, payments, _, user = payment_case
    payment = payments.reserve(user["id"], "sandbox", now=1000)
    assert payment["amount"] == 1990
    order = order_for(payment)
    payments.record_order(payment["id"], user["id"], order)
    assert subscriptions.status(user["id"], now=1000)["access_allowed"] is False
    first = payments.confirm(payment["id"], user["id"], FakeBank(order), now=1000)
    repeated = payments.confirm(payment["id"], user["id"], FakeBank(order), now=2000)
    assert first["period_end"] == 1000 + MONTH_SECONDS
    assert repeated["period_end"] == first["period_end"]
    assert subscriptions.status(user["id"], now=1000)["kind"] == "paid"
    expired = subscriptions.status(user["id"], now=first["period_end"])
    assert expired["access_allowed"] is False
    assert expired["trial_available"] is False
    assert payments.reserve(user["id"], "sandbox", now=2000)["amount"] == 2990


def test_waiting_or_wrong_value_cannot_grant_access(payment_case):
    _, subscriptions, payments, _, user = payment_case
    payment = payments.reserve(user["id"], "sandbox", now=1000)
    payments.record_order(payment["id"], user["id"], order_for(payment, "WAITING"))
    for order in (order_for(payment, "WAITING"), order_for(payment, amount=1)):
        result = payments.confirm(payment["id"], user["id"], FakeBank(order), now=1000)
        assert result["state"] == "WAITING"
        assert subscriptions.status(user["id"], now=1000)["access_allowed"] is False


def test_reservation_reuses_pending_charge(payment_case):
    _, _, payments, _, user = payment_case
    first = payments.reserve(user["id"], "sandbox", now=1000)
    repeated = payments.reserve(user["id"], "sandbox", now=1001)
    assert first["id"] == repeated["id"]
    assert first["reference"] == repeated["reference"]


def test_sandbox_payment_does_not_grant_production_access(payment_case, monkeypatch):
    _, subscriptions, payments, _, user = payment_case
    payment = payments.reserve(user["id"], "sandbox", now=1000)
    order = order_for(payment)
    payments.record_order(payment["id"], user["id"], order)
    payments.confirm(payment["id"], user["id"], FakeBank(order), now=1000)
    monkeypatch.setenv("PAGBANK_ENVIRONMENT", "production")
    assert subscriptions.status(user["id"], now=1000)["access_allowed"] is False
    assert payments.reserve(user["id"], "production", now=1001)["amount"] == 1990


def test_payment_is_private_and_admin_block_wins(payment_case):
    accounts, subscriptions, payments, admin, user = payment_case
    other = accounts.create_user("Outro", "other@example.invalid", "SenhaTeste123!")
    accounts.change_access(admin["id"], other["id"], "authorize")
    payment = payments.reserve(user["id"], "sandbox", now=1000)
    with pytest.raises(HTTPException) as error:
        payments.get(payment["id"], other["id"])
    assert error.value.status_code == 404

    order = order_for(payment)
    payments.record_order(payment["id"], user["id"], order)
    payments.confirm(payment["id"], user["id"], FakeBank(order), now=1000)
    accounts.change_access(admin["id"], user["id"], "block")
    assert subscriptions.status(user["id"], now=1001)["access_allowed"] is False
    with pytest.raises(HTTPException):
        payments.confirm(payment["id"], user["id"], FakeBank(order), now=1001)



def test_expired_waiting_pix_can_be_replaced(payment_case):
    _, subscriptions, payments, _, user = payment_case
    first = payments.reserve(user["id"], "sandbox", now=1000)
    order = order_for(first, "WAITING")
    payments.record_order(first["id"], user["id"], order)

    before = payments.confirm(
        first["id"], user["id"], FakeBank(order), now=2799
    )
    assert before["state"] == "WAITING"

    expired = payments.confirm(
        first["id"], user["id"], FakeBank(order), now=2800
    )
    assert expired["state"] == "EXPIRED"
    assert expired["qr_text"] is None
    assert subscriptions.status(user["id"], now=2800)["access_allowed"] is False

    replacement = payments.reserve(user["id"], "sandbox", now=2800)
    assert replacement["id"] != first["id"]
    assert replacement["reference"] != first["reference"]
    assert replacement["amount"] == 1990
    assert payments.get(first["id"], user["id"])["state"] == "EXPIRED"


def test_paid_pix_is_confirmed_even_when_checked_after_deadline(payment_case):
    _, subscriptions, payments, _, user = payment_case
    payment = payments.reserve(user["id"], "sandbox", now=1000)
    payments.record_order(
        payment["id"], user["id"], order_for(payment, "WAITING")
    )
    confirmed = payments.confirm(
        payment["id"], user["id"],
        FakeBank(order_for(payment)), now=2801,
    )
    assert confirmed["state"] == "PAID"
    assert subscriptions.status(user["id"], now=2801)["kind"] == "paid"


def test_wrong_bank_response_cannot_expire_pending_payment(payment_case):
    _, _, payments, _, user = payment_case
    payment = payments.reserve(user["id"], "sandbox", now=1000)
    payments.record_order(
        payment["id"], user["id"], order_for(payment, "WAITING")
    )
    wrong = order_for(payment, "WAITING", amount=1)
    result = payments.confirm(
        payment["id"], user["id"], FakeBank(wrong), now=2801
    )
    assert result["state"] == "WAITING"
    assert payments.reserve(
        user["id"], "sandbox", now=2801
    )["id"] == payment["id"]


def test_paid_member_cannot_start_unused_trial_after_month_ends(payment_case):
    _, subscriptions, payments, _, user = payment_case
    payment = payments.reserve(user["id"], "sandbox", now=1000)
    order = order_for(payment)
    payments.record_order(payment["id"], user["id"], order)
    confirmed = payments.confirm(
        payment["id"], user["id"], FakeBank(order), now=1000
    )
    status = subscriptions.start_trial(
        user["id"], now=confirmed["period_end"] + 1
    )
    assert status["trial_started_at"] is None
    assert status["trial_available"] is False
    assert status["access_allowed"] is False
    assert status["next_payment_amount"] == 2990
