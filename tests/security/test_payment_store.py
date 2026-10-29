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



def test_elapsed_local_deadline_keeps_waiting_pix_reserved(payment_case):
    _, subscriptions, payments, _, user = payment_case
    first = payments.reserve(user["id"], "sandbox", now=1000)
    order = order_for(first, "WAITING")
    payments.record_order(first["id"], user["id"], order)

    before = payments.confirm(
        first["id"], user["id"], FakeBank(order), now=2799
    )
    assert before["state"] == "WAITING"

    waiting = payments.confirm(
        first["id"], user["id"], FakeBank(order), now=2800
    )
    assert waiting["state"] == "WAITING"
    assert waiting["qr_text"] == "codigo-apenas-para-teste"
    assert subscriptions.status(user["id"], now=2800)["access_allowed"] is False

    reserved = payments.reserve(user["id"], "sandbox", now=2800)
    assert reserved["id"] == first["id"]
    assert reserved["reference"] == first["reference"]

    # A confirmacao tardia do mesmo pedido concede somente um periodo.
    confirmed = payments.confirm(
        first["id"], user["id"], FakeBank(order_for(first)), now=2801
    )
    repeated = payments.confirm(
        first["id"], user["id"], FakeBank(order_for(first)), now=2802
    )
    assert confirmed["state"] == "PAID"
    assert confirmed["period_end"] == 2801 + MONTH_SECONDS
    assert repeated["period_end"] == confirmed["period_end"]


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


def test_prepaid_renewal_shows_full_validity_and_keeps_access(payment_case):
    _, subscriptions, payments, _, user = payment_case

    first = payments.reserve(user["id"], "sandbox", now=1000)
    assert first["amount"] == 1990
    order = order_for(first)
    payments.record_order(first["id"], user["id"], order)
    first = payments.confirm(
        first["id"], user["id"], FakeBank(order), now=1000
    )

    renewal = payments.reserve(user["id"], "sandbox", now=2000)
    assert renewal["amount"] == 2990
    order = order_for(renewal)
    payments.record_order(renewal["id"], user["id"], order)
    renewal = payments.confirm(
        renewal["id"], user["id"], FakeBank(order), now=2000
    )

    assert renewal["period_start"] == first["period_end"]
    assert renewal["period_end"] == first["period_end"] + MONTH_SECONDS

    for timestamp in (
        2000,
        first["period_end"] - 1,
        first["period_end"],
        renewal["period_end"] - 1,
    ):
        status = subscriptions.status(user["id"], now=timestamp)
        assert status["kind"] == "paid"
        assert status["access_allowed"] is True
        assert status["paid_ends_at"] == renewal["period_end"]
        assert status["next_payment_amount"] == 2990

    expired = subscriptions.status(
        user["id"], now=renewal["period_end"]
    )
    assert expired["access_allowed"] is False

    repeated = payments.confirm(
        renewal["id"], user["id"], FakeBank(order), now=3000
    )
    assert repeated["period_end"] == renewal["period_end"]


def test_future_payment_does_not_bridge_unpaid_gap(payment_case):
    accounts, subscriptions, payments, _, user = payment_case

    first = payments.reserve(user["id"], "sandbox", now=1000)
    order = order_for(first)
    payments.record_order(first["id"], user["id"], order)
    first = payments.confirm(
        first["id"], user["id"], FakeBank(order), now=1000
    )

    renewal_start = first["period_end"] + 100
    renewal = payments.reserve(
        user["id"], "sandbox", now=renewal_start
    )
    order = order_for(renewal)
    payments.record_order(renewal["id"], user["id"], order)
    renewal = payments.confirm(
        renewal["id"], user["id"], FakeBank(order),
        now=renewal_start,
    )

    current = subscriptions.status(user["id"], now=2000)
    assert current["paid_ends_at"] == first["period_end"]
    assert current["access_allowed"] is True

    gap = subscriptions.status(
        user["id"], now=first["period_end"]
    )
    assert gap["access_allowed"] is False

    started = subscriptions.status(user["id"], now=renewal_start)
    assert started["access_allowed"] is True
    assert started["paid_ends_at"] == renewal["period_end"]

    with accounts.connection() as db:
        assert db.execute(
            "SELECT COUNT(*) FROM subscription_payments WHERE user_id=?",
            (user["id"],),
        ).fetchone()[0] == 2


@pytest.mark.parametrize("distinct", [False, True])
def test_concurrent_confirmations_grant_each_payment_only_once(payment_case, distinct):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    accounts, subscriptions, payments, _, user = payment_case
    first = payments.reserve(user["id"], "sandbox", now=1000)
    payments.record_order(first["id"], user["id"], order_for(first, "WAITING"))
    targets = [first, first]
    if distinct:
        # Historico criado pela regra antiga, seguido de uma substituicao.
        with accounts.connection() as db:
            db.execute("UPDATE subscription_payments SET state='EXPIRED' WHERE id=?", (first["id"],))
        second = payments.reserve(user["id"], "sandbox", now=2000)
        payments.record_order(second["id"], user["id"], order_for(second, "WAITING"))
        targets[1] = second
    orders = {order_for(payment)["id"]: order_for(payment) for payment in targets}
    barrier = Barrier(2)

    class ConcurrentBank:
        environment = "sandbox"

        def consult_order(self, order_id):
            barrier.wait(timeout=10)
            return orders[order_id]

    def confirm(payment):
        return payments.confirm(payment["id"], user["id"], ConcurrentBank(), now=3000)

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(confirm, targets))
    assert all(result["state"] == "PAID" for result in results)
    periods = sorted({(result["period_start"], result["period_end"]) for result in results})
    assert len(periods) == (2 if distinct else 1)
    assert periods[0][0] == 3000
    if distinct:
        assert periods[0][1] == periods[1][0]
    expected_end = 3000 + len(periods) * MONTH_SECONDS
    assert periods[-1][1] == expected_end
    assert subscriptions.status(user["id"], now=3000)["paid_ends_at"] == expected_end
