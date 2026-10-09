import pytest
from fastapi.testclient import TestClient

import main
from core import admin_api, auth_api
from core.accounts import AccountStore
from core.subscriptions import SubscriptionStore


@pytest.fixture
def members_case(tmp_path, monkeypatch):
    store = AccountStore(str(tmp_path / "accounts.sqlite3"))
    admin = store.create_user(
        "Admin", "admin@example.invalid", "SenhaTeste123!"
    )
    admin = store.bootstrap_admin(admin["email"], "SenhaTeste123!")
    member = store.create_user(
        "Candidato", "candidate@example.invalid", "SenhaTeste123!",
        commercial=True,
    )
    monkeypatch.setattr(auth_api, "get_store", lambda: store)
    monkeypatch.setattr(admin_api, "get_store", lambda: store)
    monkeypatch.setenv("PAGBANK_ENVIRONMENT", "sandbox")
    with TestClient(main.app) as client:
        yield store, client, admin, member


def headers(store, user):
    return {"Authorization": "Bearer " + store.issue_session(user["id"])}


def test_members_are_exclusive_to_admin(members_case):
    store, client, _, member = members_case
    assert client.get("/admin/members").status_code == 401
    assert client.get(
        "/admin/members", headers=headers(store, member)
    ).status_code == 403


def test_admin_sees_trial_dates_without_secrets(members_case):
    store, client, admin, member = members_case
    subscriptions = SubscriptionStore(store)
    started = subscriptions.start_trial(member["id"])

    response = client.get("/admin/members", headers=headers(store, admin))
    assert response.status_code == 200
    row = next(
        item for item in response.json()["members"]
        if item["id"] == member["id"]
    )
    assert row["subscription"]["kind"] == "trial"
    assert row["subscription"]["trial_ends_at"] == started["trial_ends_at"]
    assert row["email"] == member["email"]
    assert row["payments"] == []
    assert set(row) == {
        "id", "name", "email", "role", "state", "subscription", "payments",
        "access_history",
    }
    assert "password_hash" not in response.text
    assert "access_token" not in response.text


def test_admin_sees_payment_environment_and_amount(members_case):
    import time

    store, client, admin, member = members_case
    now = time.time()
    with store.connection() as db:
        db.execute(
            "INSERT INTO subscription_payments "
            "(id, user_id, environment, reference, order_id, amount, "
            "state, qr_text, created_at, period_start, period_end) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "test-payment", member["id"], "sandbox", "test-reference",
                "ORDE_test", 1990, "PAID", "private-qr-code",
                now, now, now + 30 * 86400,
            ),
        )

    response = client.get("/admin/members", headers=headers(store, admin))
    assert response.status_code == 200
    row = next(
        item for item in response.json()["members"]
        if item["id"] == member["id"]
    )
    assert row["subscription"]["kind"] == "paid"
    payment = row["payments"][0]
    assert payment["amount"] == 1990
    assert payment["environment"] == "sandbox"
    assert payment["state"] == "PAID"
    assert "qr_text" not in payment
    assert "private-qr-code" not in response.text


def test_successful_logins_are_recorded_and_failed_login_is_not(members_case):
    store, client, admin, member = members_case
    payload = {
        "email": member["email"],
        "password": "SenhaTeste123!",
    }

    def login_count():
        with store.connection() as db:
            return db.execute(
                "SELECT COUNT(*) FROM account_entry_history "
                "WHERE user_id=? AND event='LOGIN'",
                (member["id"],),
            ).fetchone()[0]

    assert login_count() == 0
    first = client.post("/auth/login", json=payload)
    assert first.status_code == 200
    assert client.post("/auth/login", json=payload).status_code == 200
    assert login_count() == 2

    wrong = client.post(
        "/auth/login",
        json={**payload, "password": "SenhaErrada123!"},
    )
    assert wrong.status_code == 401
    assert login_count() == 2

    response = client.get("/admin/members", headers=headers(store, admin))
    assert response.status_code == 200
    row = next(
        item for item in response.json()["members"]
        if item["id"] == member["id"]
    )
    assert sum(
        entry["event"] == "LOGIN" for entry in row["access_history"]
    ) == 2
    assert sum(
        entry["event"] == "REGISTER" for entry in row["access_history"]
    ) == 1
    assert all(entry["occurred_at"] > 0 for entry in row["access_history"])
    assert first.json()["access_token"] not in response.text
    assert payload["password"] not in response.text
