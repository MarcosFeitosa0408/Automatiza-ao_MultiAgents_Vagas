import pytest
from fastapi import HTTPException

from core.accounts import AccountStore


@pytest.fixture
def subscription_case(tmp_path):
    from core.subscriptions import SubscriptionStore

    accounts = AccountStore(str(tmp_path / "accounts.sqlite3"))
    admin = accounts.create_user(
        "Administrador", "admin@example.invalid", "SenhaTeste123!"
    )
    accounts.bootstrap_admin(admin["email"], "SenhaTeste123!")
    user = accounts.create_user(
        "Candidato", "candidate@example.invalid", "SenhaTeste123!"
    )
    accounts.change_access(admin["id"], user["id"], "authorize")
    return accounts, SubscriptionStore(accounts), admin, user


def test_existing_account_keeps_access(subscription_case):
    _, subscriptions, _, user = subscription_case

    status = subscriptions.status(user["id"], now=1000)

    assert status["access_allowed"] is True
    assert status["kind"] == "existing"


def test_trial_lasts_24_hours_and_cannot_restart(subscription_case):
    accounts, subscriptions, _, user = subscription_case
    subscriptions.enroll(user["id"])

    initial = subscriptions.status(user["id"], now=1000)
    assert initial["access_allowed"] is False
    assert initial["trial_available"] is True

    started = subscriptions.start_trial(user["id"], now=1000)
    assert started["access_allowed"] is True
    assert started["trial_ends_at"] == 1000 + 86400

    reloaded = SubscriptionStore_for_test(accounts)
    repeated = reloaded.start_trial(user["id"], now=2000)
    assert repeated["trial_ends_at"] == started["trial_ends_at"]

    expired = reloaded.status(user["id"], now=1000 + 86400)
    assert expired["access_allowed"] is False
    assert expired["trial_available"] is False

    attempted = reloaded.start_trial(user["id"], now=1000 + 86401)
    assert attempted["access_allowed"] is False
    assert attempted["trial_ends_at"] == started["trial_ends_at"]


def SubscriptionStore_for_test(accounts):
    from core.subscriptions import SubscriptionStore

    return SubscriptionStore(accounts)


def test_blocked_account_cannot_start_trial(subscription_case):
    accounts, subscriptions, admin, user = subscription_case
    subscriptions.enroll(user["id"])
    accounts.change_access(admin["id"], user["id"], "block")

    with pytest.raises(HTTPException) as error:
        subscriptions.start_trial(user["id"], now=1000)

    assert error.value.status_code == 403
    assert subscriptions.status(user["id"], now=1000)["access_allowed"] is False


def test_trial_expiration_preserves_profile_and_jobs(subscription_case):
    accounts, subscriptions, _, user = subscription_case
    subscriptions.enroll(user["id"])

    with accounts.connection() as db:
        profile_before = db.execute(
            "SELECT payload FROM profiles WHERE user_id=?", (user["id"],)
        ).fetchone()["payload"]
        db.execute(
            "INSERT INTO private_applications VALUES (?, ?, ?)",
            (user["id"], "preserved-job", '{"history": ["SCREENING"]}'),
        )

    subscriptions.start_trial(user["id"], now=1000)
    assert subscriptions.status(
        user["id"], now=1000 + 86400
    )["access_allowed"] is False

    with accounts.connection() as db:
        assert db.execute(
            "SELECT payload FROM profiles WHERE user_id=?", (user["id"],)
        ).fetchone()["payload"] == profile_before
        assert db.execute(
            "SELECT payload FROM private_applications WHERE user_id=?",
            (user["id"],),
        ).fetchone()["payload"] == '{"history": ["SCREENING"]}'
        assert db.execute(
            "SELECT state FROM account_access WHERE user_id=?", (user["id"],)
        ).fetchone()["state"] == "active"


def test_admin_access_is_preserved(subscription_case):
    _, subscriptions, admin, _ = subscription_case

    with pytest.raises(HTTPException) as error:
        subscriptions.enroll(admin["id"])
    assert error.value.status_code == 403

    status = subscriptions.start_trial(admin["id"], now=1000)
    assert status["kind"] == "admin"
    assert status["access_allowed"] is True
    assert status["trial_available"] is False


def test_pending_account_cannot_start_trial(subscription_case):
    accounts, subscriptions, _, _ = subscription_case
    pending = accounts.create_user(
        "Pendente", "pending@example.invalid", "SenhaTeste123!"
    )
    subscriptions.enroll(pending["id"])

    with pytest.raises(HTTPException) as error:
        subscriptions.start_trial(pending["id"], now=1000)
    assert error.value.status_code == 403

    status = subscriptions.status(pending["id"], now=1000)
    assert status["access_allowed"] is False
    assert status["trial_started_at"] is None


def test_simultaneous_clicks_and_enrollment_do_not_extend_trial(subscription_case):
    from concurrent.futures import ThreadPoolExecutor

    _, subscriptions, _, user = subscription_case
    subscriptions.enroll(user["id"])

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(
            lambda timestamp: subscriptions.start_trial(
                user["id"], now=timestamp
            ),
            [1000, 1001],
        ))

    assert results[0]["trial_ends_at"] == results[1]["trial_ends_at"]
    assert results[0]["trial_started_at"] in (1000, 1001)

    subscriptions.enroll(user["id"])
    status = subscriptions.status(user["id"], now=2000)
    assert status["trial_ends_at"] == results[0]["trial_ends_at"]


def test_seven_days_of_consultation_after_trial(subscription_case):
    _, subscriptions, _, user = subscription_case
    subscriptions.enroll(user["id"])
    subscriptions.start_trial(user["id"], now=1000)
    trial_end = 1000 + 86400
    consultation_end = trial_end + 7 * 86400

    trial = subscriptions.status(user["id"], now=trial_end - 1)
    assert trial["access_allowed"] is True
    assert trial["read_allowed"] is True

    consultation = subscriptions.status(user["id"], now=trial_end)
    assert consultation["kind"] == "consultation"
    assert consultation["access_allowed"] is False
    assert consultation["read_allowed"] is True
    assert consultation["trial_available"] is False
    assert consultation["consultation_ends_at"] == consultation_end

    last_second = subscriptions.status(
        user["id"], now=consultation_end - 1
    )
    assert last_second["read_allowed"] is True

    expired = subscriptions.status(user["id"], now=consultation_end)
    assert expired["kind"] == "trial_expired"
    assert expired["access_allowed"] is False
    assert expired["read_allowed"] is False

    repeated = subscriptions.start_trial(
        user["id"], now=consultation_end + 1
    )
    assert repeated["trial_ends_at"] == trial_end
    assert repeated["consultation_ends_at"] == consultation_end
    assert repeated["read_allowed"] is False


def test_admin_block_overrides_consultation(subscription_case):
    accounts, subscriptions, admin, user = subscription_case
    subscriptions.enroll(user["id"])
    subscriptions.start_trial(user["id"], now=1000)
    accounts.change_access(admin["id"], user["id"], "block")

    status = subscriptions.status(user["id"], now=1000 + 86400)
    assert status["access_allowed"] is False
    assert status["read_allowed"] is False
