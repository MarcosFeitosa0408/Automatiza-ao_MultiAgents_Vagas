"""Mensalidades privadas. Confirmacao sempre consultada no PagBank."""
import re
import time
from uuid import uuid4

from fastapi import HTTPException
from core.pagbank import payment_is_confirmed

MONTH_SECONDS = 30 * 86400


class PaymentStore:
    def __init__(self, accounts):
        self.accounts = accounts
        with accounts.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("""
                CREATE TABLE IF NOT EXISTS subscription_payments (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    environment TEXT NOT NULL
                        CHECK(environment IN ('sandbox', 'production')),
                    reference TEXT UNIQUE NOT NULL,
                    order_id TEXT,
                    amount INTEGER NOT NULL CHECK(amount IN (1990, 2990)),
                    state TEXT NOT NULL
                        CHECK(state IN ('CREATING', 'WAITING', 'PAID',
                                        'DECLINED', 'CANCELED', 'EXPIRED')),
                    qr_text TEXT,
                    created_at DOUBLE PRECISION NOT NULL,
                    period_start DOUBLE PRECISION,
                    period_end DOUBLE PRECISION,
                    UNIQUE(environment, order_id)
                )
            """)

    def reserve(self, user_id, environment, *, now=None):
        if environment not in ("sandbox", "production"):
            raise ValueError("Ambiente invalido.")
        timestamp = time.time() if now is None else now
        with self.accounts.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            self._active_member(db, user_id)
            enrolled = db.execute(
                "SELECT user_id FROM subscriptions WHERE user_id=?",
                (user_id,),
            ).fetchone()
            if not enrolled:
                raise HTTPException(409, "Esta conta nao pertence ao plano comercial.")

            pending = db.execute("""
                SELECT * FROM subscription_payments
                WHERE user_id=? AND environment=?
                    AND state IN ('CREATING', 'WAITING')
                ORDER BY created_at DESC LIMIT 1
            """, (user_id, environment)).fetchone()
            if pending:
                return dict(pending)

            paid = db.execute("""
                SELECT COUNT(*) FROM subscription_payments
                WHERE user_id=? AND environment=? AND state='PAID'
            """, (user_id, environment)).fetchone()[0]
            payment_id = str(uuid4())
            reference = "payment-" + uuid4().hex
            amount = 2990 if paid else 1990
            db.execute("""
                INSERT INTO subscription_payments (
                    id, user_id, environment, reference, amount,
                    state, created_at
                ) VALUES (?, ?, ?, ?, ?, 'CREATING', ?)
            """, (
                payment_id, user_id, environment, reference, amount, timestamp,
            ))
            return dict(self._payment(db, payment_id, user_id))

    def expire_rejected_creation(self, payment_id, user_id):
        """Uso interno, somente apos rejeicao explicita do PagBank."""
        with self.accounts.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            self._active_member(db, user_id)
            row = self._payment(db, payment_id, user_id)
            if row["state"] != "CREATING" or row["order_id"] is not None:
                return False
            db.execute(
                "UPDATE subscription_payments SET state='EXPIRED' "
                "WHERE id=? AND user_id=? AND state='CREATING' "
                "AND order_id IS NULL",
                (payment_id, user_id),
            )
            return True

    def record_order(self, payment_id, user_id, order):
        """Uso interno: recebe a resposta da criacao feita pelo servidor."""
        with self.accounts.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            self._active_member(db, user_id)
            row = self._payment(db, payment_id, user_id)
            if row["state"] != "CREATING":
                return dict(row)

            order_id = order.get("id", "")
            charges = order.get("charges", [])
            if (
                not isinstance(order_id, str)
                or not re.fullmatch(r"ORDE_[A-Za-z0-9-]{1,80}", order_id)
                or order.get("reference_id") != row["reference"]
                or not isinstance(charges, list)
                or len(charges) != 1
            ):
                raise HTTPException(502, "Pedido retornado pelo banco nao corresponde a cobranca.")
            charge = charges[0]
            if not isinstance(charge, dict):
                raise HTTPException(502, "Cobranca retornada pelo banco invalida.")
            amount = charge.get("amount") or {}
            if (
                charge.get("reference_id") != row["reference"]
                or not isinstance(amount, dict)
                or amount.get("value") != row["amount"]
                or amount.get("currency") != "BRL"
            ):
                raise HTTPException(502, "Valor ou referencia da cobranca divergente.")

            status = charge.get("status")
            if status not in ("WAITING", "PAID", "DECLINED", "CANCELED"):
                raise HTTPException(502, "Status de cobranca nao reconhecido.")
            # Mesmo PAID na criacao exige consulta independente antes de liberar.
            state = "WAITING" if status in ("WAITING", "PAID") else status
            qr = charge.get("qr_code") or {}
            qr_text = qr.get("text") if isinstance(qr, dict) else None
            if qr_text is not None and (
                not isinstance(qr_text, str) or len(qr_text) > 10000
            ):
                raise HTTPException(502, "Codigo Pix retornado invalido.")

            db.execute("""
                UPDATE subscription_payments SET order_id=?, state=?, qr_text=?
                WHERE id=? AND user_id=?
            """, (order_id, state, qr_text, payment_id, user_id))
            return dict(self._payment(db, payment_id, user_id))

    def confirm(self, payment_id, user_id, client, *, now=None):
        timestamp = time.time() if now is None else now
        with self.accounts.connection() as db:
            self._active_member(db, user_id)
            row = dict(self._payment(db, payment_id, user_id))
        if row["environment"] != client.environment:
            raise HTTPException(409, "Ambiente de pagamento divergente.")
        if not row["order_id"]:
            raise HTTPException(409, "A cobranca ainda nao foi criada.")

        # Consulta fora da transacao: nao prende o banco durante a chamada externa.
        order = client.consult_order(row["order_id"])
        if not payment_is_confirmed(
            order,
            order_id=row["order_id"],
            reference=row["reference"],
            amount=row["amount"],
        ):
            # Somente uma resposta correspondente do banco pode encerrar
            # a cobranca pendente. Pagamento confirmado tem prioridade.
            charges = order.get("charges", []) if isinstance(order, dict) else []
            charge = (
                charges[0]
                if isinstance(charges, list) and len(charges) == 1
                and isinstance(charges[0], dict)
                else {}
            )
            amount = charge.get("amount") or {}
            summary = amount.get("summary") or {} if isinstance(amount, dict) else {}
            method = charge.get("payment_method") or {}
            matches = (
                isinstance(order, dict)
                and order.get("id") == row["order_id"]
                and order.get("reference_id") == row["reference"]
                and charge.get("reference_id") == row["reference"]
                and isinstance(method, dict)
                and method.get("type") == "PIX"
                and isinstance(amount, dict)
                and amount.get("value") == row["amount"]
                and amount.get("currency") == "BRL"
                and isinstance(summary, dict)
                and summary.get("paid") == 0
                and summary.get("refunded", 0) == 0
            )
            state = charge.get("status")
            terminal = None
            if matches and state in ("DECLINED", "CANCELED"):
                terminal = state
            elif (
                matches
                and state == "WAITING"
                and timestamp >= row["created_at"] + 1800
            ):
                terminal = "EXPIRED"

            if terminal:
                with self.accounts.connection() as db:
                    db.execute("BEGIN IMMEDIATE")
                    self._active_member(db, user_id)
                    db.execute(
                        "UPDATE subscription_payments "
                        "SET state=?, qr_text=NULL "
                        "WHERE id=? AND user_id=? AND state='WAITING'",
                        (terminal, payment_id, user_id),
                    )
            return self.get(payment_id, user_id)

        with self.accounts.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            self._active_member(db, user_id)
            current = self._payment(db, payment_id, user_id)
            if current["state"] == "PAID":
                return dict(current)

            previous = db.execute("""
                SELECT MAX(period_end) FROM subscription_payments
                WHERE user_id=? AND environment=? AND state='PAID'
            """, (user_id, client.environment)).fetchone()[0]
            trial = db.execute(
                "SELECT trial_ends_at FROM subscriptions WHERE user_id=?",
                (user_id,),
            ).fetchone()
            start = max(
                timestamp,
                previous or timestamp,
                trial["trial_ends_at"] if trial and trial["trial_ends_at"] else timestamp,
            )
            db.execute("""
                UPDATE subscription_payments
                SET state='PAID', period_start=?, period_end=?
                WHERE id=? AND user_id=?
            """, (start, start + MONTH_SECONDS, payment_id, user_id))
            return dict(self._payment(db, payment_id, user_id))

    def get(self, payment_id, user_id):
        with self.accounts.connection() as db:
            self._active_member(db, user_id)
            return dict(self._payment(db, payment_id, user_id))

    def _payment(self, db, payment_id, user_id):
        row = db.execute("""
            SELECT * FROM subscription_payments WHERE id=? AND user_id=?
        """, (payment_id, user_id)).fetchone()
        if row is None:
            raise HTTPException(404, "Pagamento nao encontrado.")
        return row

    def _active_member(self, db, user_id):
        user = self.accounts._user(db, user_id)
        if not user or user["state"] != "active" or user["role"] == "admin":
            raise HTTPException(403, "Conta indisponivel para esta operacao.")
