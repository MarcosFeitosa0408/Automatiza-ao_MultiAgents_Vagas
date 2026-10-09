import time

import pytest
from fastapi.testclient import TestClient

import main
from core import auth_api, subscription_api
from core.accounts import AccountStore
from core.subscriptions import SubscriptionStore


@pytest.fixture
def subscription_api_case(tmp_path, monkeypatch):
    store = AccountStore(str(tmp_path / "accounts.sqlite3"))
    monkeypatch.setattr(auth_api, "get_store", lambda: store)
    monkeypatch.setattr(subscription_api, "get_store", lambda: store)

    admin = store.create_user(
        "Admin", "admin@example.invalid", "SenhaTeste123!"
    )
    store.bootstrap_admin(admin["email"], "SenhaTeste123!")

    users = []
    for email in ("a@example.invalid", "b@example.invalid"):
        user = store.create_user("Teste", email, "SenhaTeste123!")
        store.change_access(admin["id"], user["id"], "authorize")
        users.append(user)

    subscriptions = SubscriptionStore(store)
    with TestClient(main.app) as client:
        yield store, subscriptions, client, users


def auth_headers(store, user):
    return {"Authorization": "Bearer " + store.issue_session(user["id"])}


def test_subscription_api_requires_authentication(subscription_api_case):
    _, _, client, _ = subscription_api_case

    assert client.get("/auth/subscription").status_code == 401
    assert client.post("/auth/trial").status_code == 401


def test_trial_api_is_scoped_and_cannot_restart(subscription_api_case):
    store, subscriptions, client, (a, b) = subscription_api_case
    subscriptions.enroll(a["id"])
    subscriptions.enroll(b["id"])
    a_headers = auth_headers(store, a)
    b_headers = auth_headers(store, b)

    initial = client.get("/auth/subscription", headers=a_headers)
    assert initial.status_code == 200
    assert initial.json()["trial_available"] is True

    started = client.post("/auth/trial", headers=a_headers)
    assert started.status_code == 200
    assert started.json()["access_allowed"] is True

    other = client.get("/auth/subscription", headers=b_headers).json()
    assert other["trial_started_at"] is None
    assert other["access_allowed"] is False

    repeated = client.post("/auth/trial", headers=a_headers).json()
    assert repeated["trial_ends_at"] == started.json()["trial_ends_at"]

    expired_start = time.time() - 86401
    with store.connection() as db:
        db.execute(
            "UPDATE subscriptions SET trial_started_at=?, trial_ends_at=? "
            "WHERE user_id=?",
            (expired_start, expired_start + 86400, a["id"]),
        )

    expired_response = client.post("/auth/trial", headers=a_headers)
    assert expired_response.status_code == 200
    expired = expired_response.json()
    assert expired["access_allowed"] is False
    assert expired["trial_available"] is False
    assert expired["trial_ends_at"] == expired_start + 86400


def test_blocking_revokes_trial_api_access(subscription_api_case):
    store, subscriptions, client, (a, _) = subscription_api_case
    subscriptions.enroll(a["id"])
    token_headers = auth_headers(store, a)
    assert client.post("/auth/trial", headers=token_headers).status_code == 200

    with store.connection() as db:
        admin_id = db.execute(
            "SELECT user_id FROM account_access WHERE role='admin'"
        ).fetchone()["user_id"]

    store.change_access(admin_id, a["id"], "block")
    assert client.get(
        "/auth/subscription", headers=token_headers
    ).status_code == 401
    assert client.post(
        "/auth/trial", headers=token_headers
    ).status_code == 401


def test_consultation_allows_reading_but_prevents_actions(
    subscription_api_case, monkeypatch
):
    from fastapi.routing import APIRoute

    store, subscriptions, client, (user, _) = subscription_api_case
    monkeypatch.setattr(main, "get_store", lambda: store)
    subscriptions.enroll(user["id"])
    subscriptions.start_trial(user["id"], now=time.time() - 86401)
    headers = auth_headers(store, user)

    assert client.get("/auth/me", headers=headers).status_code == 200
    status = client.get("/auth/subscription", headers=headers).json()
    assert status["kind"] == "consultation"

    readable = {
        "/profile",
        "/job-applications",
        "/job-applications/metrics",
        "/job-applications/{application_id}",
    }

    for path in ("/profile", "/job-applications", "/job-applications/metrics"):
        assert client.get(path, headers=headers).status_code == 200

    assert client.get(
        "/job-applications/not-found", headers=headers
    ).status_code == 404

    for route in main.app.routes:
        if not isinstance(route, APIRoute):
            continue
        if route.path == "/health" or route.path.startswith(
            ("/auth/", "/help/", "/admin/")
        ):
            continue

        path = route.path.replace("{application_id}", "not-found")
        for method in route.methods:
            if method == "GET" and route.path in readable:
                continue
            response = client.request(
                method, path, headers=headers, json={}
            )
            assert response.status_code == 402, (
                method, path, response.text
            )


def test_after_consultation_only_account_access_remains(
    subscription_api_case, monkeypatch
):
    store, subscriptions, client, (user, _) = subscription_api_case
    monkeypatch.setattr(main, "get_store", lambda: store)
    subscriptions.enroll(user["id"])
    subscriptions.start_trial(user["id"], now=time.time() - 8 * 86400 - 1)
    headers = auth_headers(store, user)

    for path in ("/profile", "/job-applications", "/job-applications/metrics"):
        assert client.get(path, headers=headers).status_code == 402

    status = client.get("/auth/subscription", headers=headers)
    assert status.status_code == 200
    assert status.json()["kind"] == "trial_expired"
    assert client.get("/auth/me", headers=headers).status_code == 200
    assert client.post("/auth/logout", headers=headers).status_code == 200


def test_existing_account_keeps_platform_access(
    subscription_api_case, monkeypatch
):
    store, _, client, (user, _) = subscription_api_case
    monkeypatch.setattr(main, "get_store", lambda: store)
    headers = auth_headers(store, user)

    profile = client.get("/profile", headers=headers)
    assert profile.status_code == 200
    assert client.put(
        "/profile", headers=headers, json=profile.json()
    ).status_code == 200
    assert client.get("/job-applications", headers=headers).status_code == 200
