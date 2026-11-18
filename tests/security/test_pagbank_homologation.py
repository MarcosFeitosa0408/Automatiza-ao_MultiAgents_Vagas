import io
import json
import logging
from copy import deepcopy
from urllib.error import HTTPError, URLError

import pytest
from fastapi import HTTPException

from core import pagbank
from core.pagbank_homologation import PREFIX, redact


@pytest.fixture
def capture_case(monkeypatch, caplog):
    monkeypatch.setenv("PAGBANK_ENVIRONMENT", "sandbox")
    monkeypatch.setenv("PAGBANK_TOKEN", "TOKEN-SECRETO-DE-TESTE-123")
    monkeypatch.setenv("PAGBANK_HOMOLOGATION_LOG_ENABLED", "true")
    caplog.set_level(logging.WARNING)
    payload = {
        "reference_id": "payment-test",
        "customer": {"name": "Nome Privado", "email": "private@example.invalid", "tax_id": "12345678909"},
        "charges": [{"amount": {"value": 1990, "currency": "BRL"}}],
    }
    order = {
        "id": "ORDE_test", "reference_id": "payment-test",
        "customer": deepcopy(payload["customer"]),
        "charges": [{"status": "WAITING", "amount": {"value": 1990, "currency": "BRL"}, "qr_code": {"text": "QR-PRIVADO"}}],
        "links": [{"href": "https://example.invalid/TOKEN-SECRETO-DE-TESTE-123"}],
    }
    class Response:
        status = 201
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def read(self, limit):
            return json.dumps(order).encode()
    class Opener:
        def open(self, request, timeout):
            assert request.get_header("Authorization") == "Bearer TOKEN-SECRETO-DE-TESTE-123"
            assert request.get_header("X-idempotency-key") == "payment-test"
            return Response()
    monkeypatch.setattr(pagbank, "build_opener", lambda *args: Opener())
    return pagbank.PagBankClient(), payload, order


def entries(caplog):
    return [json.loads(r.message.split(PREFIX, 1)[1]) for r in caplog.records if PREFIX in r.message]


def test_records_real_payload_and_response_without_secrets(capture_case, caplog):
    client, payload, order = capture_case
    original = deepcopy(payload)
    assert client._request("/orders", payload=payload, reference="payment-test") == order
    assert payload == original
    events = entries(caplog)
    assert len(events) == 2
    assert events[0]["capture_id"] == events[1]["capture_id"]
    assert events[0]["request_body"]["charges"][0]["amount"]["value"] == 1990
    assert events[1]["http_status"] == 201
    assert events[1]["response_body"]["charges"][0]["status"] == "WAITING"
    for secret in (client.token, "Nome Privado", "private@example.invalid", "12345678909", "QR-PRIVADO"):
        assert secret not in caplog.text


def test_capture_disabled_by_default(capture_case, monkeypatch, caplog):
    client, payload, order = capture_case
    monkeypatch.delenv("PAGBANK_HOMOLOGATION_LOG_ENABLED")
    assert client._request("/orders", payload=payload, reference="payment-test") == order
    assert entries(caplog) == []


def test_get_paid_keeps_actual_state(capture_case, caplog):
    client, _, order = capture_case
    order["charges"][0]["status"] = "PAID"
    # GET nao envia nem depende de chave de idempotencia.
    class Opener:
        def open(self, request, timeout):
            assert request.get_method() == "GET"
            response = io.BytesIO(json.dumps(order).encode())
            response.status = 200
            return response
    from unittest.mock import patch
    with patch.object(pagbank, "build_opener", return_value=Opener()):
        assert client.consult_order("ORDE_test") == order
    assert entries(caplog)[0]["request_body"] is None
    assert entries(caplog)[1]["http_status"] == 200
    assert entries(caplog)[1]["response_body"]["charges"][0]["status"] == "PAID"


@pytest.mark.parametrize("error", [URLError("TOKEN-SECRETO-DE-TESTE-123"), TimeoutError("private@example.invalid")])
def test_ambiguous_failure_is_not_retried_or_exposed(capture_case, caplog, error):
    client, payload, _ = capture_case
    from unittest.mock import Mock, patch
    opener = Mock()
    opener.open.side_effect = error
    with patch.object(pagbank, "build_opener", return_value=opener):
        with pytest.raises(HTTPException) as failed:
            client._request("/orders", payload=payload, reference="payment-test")
    assert failed.value.status_code == 502
    assert opener.open.call_count == 1
    assert entries(caplog)[1]["event"] == "error"
    assert client.token not in caplog.text
    assert "private@example.invalid" not in caplog.text


def test_expiration_recovery_still_receives_error_body(capture_case, caplog):
    client, payload, _ = capture_case
    body = {"error_messages": [{"code": "40002", "parameter_name": "charges[0].payment_method.pix.expiration_date", "description": "must be a future date"}]}
    error = HTTPError("https://sandbox.api.pagseguro.com/orders", 400, "Bad Request", {}, io.BytesIO(json.dumps(body).encode()))
    from unittest.mock import Mock, patch
    opener = Mock()
    opener.open.side_effect = error
    with patch.object(pagbank, "build_opener", return_value=opener):
        with pytest.raises(pagbank.PixExpirationRejected):
            client._request("/orders", payload=payload, reference="payment-test")
    assert entries(caplog)[1]["http_status"] == 400


def test_redaction_is_recursive_and_does_not_mutate():
    value = {"Authorization": "Bearer secret", "data": [{"client_secret": "private", "message": "secret Bearer abc123"}]}
    original = deepcopy(value)
    safe = json.dumps(redact(value, "secret"))
    assert value == original
    for secret in ("secret", "private", "abc123"):
        # O nome client_secret e preservado; somente seu valor e ocultado.
        if secret != "secret":
            assert secret not in safe
    assert redact(value, "secret")["data"][0]["message"] == "[OCULTO] Bearer [OCULTO]"
