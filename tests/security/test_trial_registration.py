import pytest
from fastapi.testclient import TestClient

import main
from core import auth_api, subscription_api
from core.accounts import AccountStore
from core.subscriptions import SubscriptionStore


@pytest.fixture
def trial_registration_case(tmp_path, monkeypatch):
    store = AccountStore(str(tmp_path / "accounts.sqlite3"))
    admin = store.create_user(
        "Admin", "admin@example.invalid", "SenhaTeste123!"
    )
    store.bootstrap_admin(admin["email"], "SenhaTeste123!")
    monkeypatch.setattr(auth_api, "get_store", lambda: store)
    monkeypatch.setattr(subscription_api, "get_store", lambda: store)
    with TestClient(main.app) as client:
        yield store, client, admin


def register_payload():
    return {
        "name": "Candidato de teste",
        "email": "candidate@example.invalid",
        "password": "SenhaTeste123!",
    }


def test_new_account_requires_trial_activation_and_trial_cannot_restart(
    trial_registration_case,
):
    store, client, _ = trial_registration_case
    response = client.post("/auth/register-trial", json=register_payload())
    assert response.status_code == 201
    session = response.json()
    assert session["user"]["state"] == "active"
    assert session["user"]["role"] == "user"
    headers = {"Authorization": "Bearer " + session["access_token"]}

    initial = client.get("/auth/subscription", headers=headers).json()
    assert initial["access_allowed"] is False
    assert initial["trial_available"] is True
    assert initial["trial_started_at"] is None

    started = client.post("/auth/trial", headers=headers).json()
    assert started["access_allowed"] is True
    assert started["kind"] == "trial"
    assert started["trial_ends_at"] - started["trial_started_at"] == 86400

    repeated = client.post("/auth/trial", headers=headers).json()
    assert repeated["trial_ends_at"] == started["trial_ends_at"]
    persisted = SubscriptionStore(store).status(session["user"]["id"])
    assert persisted["trial_ends_at"] == started["trial_ends_at"]


def test_duplicate_registration_does_not_authorize_existing_pending_account(
    trial_registration_case,
):
    store, client, _ = trial_registration_case
    payload = register_payload()
    old = store.create_user(
        payload["name"], payload["email"], payload["password"]
    )

    response = client.post("/auth/register-trial", json=payload)
    assert response.status_code == 409
    with store.connection() as db:
        assert store._user(db, old["id"])["state"] == "pending"
        assert db.execute(
            "SELECT user_id FROM subscriptions WHERE user_id=?",
            (old["id"],),
        ).fetchone() is None


def test_candidate_cannot_request_admin_role(trial_registration_case):
    _, client, _ = trial_registration_case
    response = client.post(
        "/auth/register-trial",
        json={**register_payload(), "role": "admin"},
    )
    assert response.status_code == 422


def test_admin_block_still_revokes_new_candidate_access(
    trial_registration_case,
):
    store, client, admin = trial_registration_case
    session = client.post(
        "/auth/register-trial", json=register_payload()
    ).json()
    headers = {"Authorization": "Bearer " + session["access_token"]}
    store.change_access(admin["id"], session["user"]["id"], "block")
    assert client.post("/auth/trial", headers=headers).status_code == 401
    assert client.get("/auth/subscription", headers=headers).status_code == 401
