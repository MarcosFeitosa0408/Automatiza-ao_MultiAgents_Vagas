"""Controle de teste gratuito, separado da autorização administrativa."""
import time
import os

from fastapi import HTTPException

from core.accounts import AccountStore


TRIAL_SECONDS = 24 * 60 * 60
CONSULTATION_SECONDS = 7 * 24 * 60 * 60


class SubscriptionStore:
    def __init__(self, accounts: AccountStore):
        self.accounts = accounts
        with accounts.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    user_id TEXT PRIMARY KEY
                        REFERENCES users(id) ON DELETE CASCADE,
                    trial_started_at DOUBLE PRECISION,
                    trial_ends_at DOUBLE PRECISION,
                    CHECK (
                        (trial_started_at IS NULL AND trial_ends_at IS NULL)
                        OR
                        (trial_started_at IS NOT NULL
                         AND trial_ends_at IS NOT NULL
                         AND trial_ends_at > trial_started_at)
                    )
                )
            """)

        from core.payment_store import PaymentStore
        PaymentStore(accounts)

    def enroll(self, user_id: str):
        """Uso interno: inclui uma conta no modelo comercial sem iniciar o teste."""
        with self.accounts.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            user = self.accounts._user(db, user_id)
            if user is None:
                raise HTTPException(404, "Conta não encontrada.")
            if user["role"] == "admin":
                raise HTTPException(403, "A conta administrativa está protegida.")
            db.execute("""
                INSERT INTO subscriptions (
                    user_id, trial_started_at, trial_ends_at
                ) VALUES (?, NULL, NULL)
                ON CONFLICT(user_id) DO NOTHING
            """, (user_id,))

    def status(self, user_id: str, *, now: float | None = None):
        current_time = time.time() if now is None else now
        with self.accounts.connection() as db:
            return self._status(db, user_id, current_time)

    def start_trial(self, user_id: str, *, now: float | None = None):
        current_time = time.time() if now is None else now
        with self.accounts.connection() as db:
            # SQLite e o adaptador Postgres serializam esta transação.
            db.execute("BEGIN IMMEDIATE")
            user = self.accounts._user(db, user_id)
            if user is None:
                raise HTTPException(404, "Conta não encontrada.")
            if user["state"] != "active":
                raise HTTPException(403, "Esta conta não está autorizada.")

            # Não inclui contas existentes no modelo comercial implicitamente.
            # Uma segunda chamada nunca renova o prazo já registrado.
            if user["role"] != "admin":
                db.execute("""
                    UPDATE subscriptions
                    SET trial_started_at=?, trial_ends_at=?
                    WHERE user_id=? AND trial_started_at IS NULL
                    AND NOT EXISTS (
                        SELECT 1 FROM subscription_payments
                        WHERE user_id=? AND environment=? AND state='PAID'
                    )
                """, (
                    current_time,
                    current_time + TRIAL_SECONDS,
                    user_id,
                    user_id,
                    os.getenv("PAGBANK_ENVIRONMENT", "").strip(),
                ))
            return self._status(db, user_id, current_time)

    def _status(self, db, user_id: str, now: float):
        user = self.accounts._user(db, user_id)
        if user is None:
            raise HTTPException(404, "Conta não encontrada.")

        row = db.execute("""
            SELECT trial_started_at, trial_ends_at
            FROM subscriptions WHERE user_id=?
        """, (user_id,)).fetchone()

        result = {
            "access_allowed": False,
            "read_allowed": False,
            "consultation_ends_at": (
                row["trial_ends_at"] + CONSULTATION_SECONDS
                if row and row["trial_ends_at"] is not None else None
            ),
            "kind": "restricted",
            "trial_available": False,
            "trial_started_at": row["trial_started_at"] if row else None,
            "trial_ends_at": row["trial_ends_at"] if row else None,
        }

        if user["state"] != "active":
            result["kind"] = user["state"]
            return result

        if user["role"] == "admin":
            result.update(access_allowed=True, read_allowed=True, kind="admin")
            return result

        if row is None:
            result.update(access_allowed=True, read_allowed=True, kind="existing")
            return result

        environment = os.getenv("PAGBANK_ENVIRONMENT", "").strip()
        paid = db.execute(
            "SELECT MAX(period_end) FROM subscription_payments "
            "WHERE user_id=? AND environment=? AND state='PAID' "
            "AND period_start<=?",
            (user_id, environment, now),
        ).fetchone()[0]
        paid_count = db.execute(
            "SELECT COUNT(*) FROM subscription_payments "
            "WHERE user_id=? AND environment=? AND state='PAID'",
            (user_id, environment),
        ).fetchone()[0]
        result["paid_ends_at"] = paid
        result["next_payment_amount"] = 2990 if paid_count else 1990

        if paid is not None and now < paid:
            result.update(access_allowed=True, read_allowed=True, kind="paid")
            return result

        if paid_count and row["trial_started_at"] is None:
            result["kind"] = "paid_expired"
            return result

        if row["trial_started_at"] is None:
            result.update(kind="trial_available", trial_available=True)
            return result

        if row["trial_started_at"] <= now < row["trial_ends_at"]:
            result.update(access_allowed=True, read_allowed=True, kind="trial")
        elif (
            row["trial_ends_at"] <= now
            < row["trial_ends_at"] + CONSULTATION_SECONDS
        ):
            result.update(read_allowed=True, kind="consultation")
        else:
            result["kind"] = "trial_expired"
        return result
