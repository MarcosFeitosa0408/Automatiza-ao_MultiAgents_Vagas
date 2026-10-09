import io
import json
from urllib.error import HTTPError, URLError

import pytest
from fastapi import HTTPException
from core import pagbank


@pytest.mark.parametrize(
    "body, expected",
    [
        ({"error_messages": [{
            "code": "40002",
            "description": "must be a future date",
            "parameter_name": "charges[0].payment_method.pix.expiration_date",
        }]}, True),
        ({"error_messages": [{
            "code": "40002",
            "description": "invalid_parameter",
            "parameter_name": "customer.tax_id",
        }]}, False),
        ({}, False),
    ],
)
def test_only_explicit_expiration_rejection_can_replace_request(
    monkeypatch, body, expected
):
    monkeypatch.setenv("PAGBANK_ENVIRONMENT", "sandbox")
    monkeypatch.setenv("PAGBANK_TOKEN", "token-apenas-de-teste")

    class FakeOpener:
        def open(self, request, timeout):
            raise HTTPError(
                request.full_url, 400, "Bad Request", {},
                io.BytesIO(json.dumps(body).encode()),
            )

    monkeypatch.setattr(pagbank, "build_opener", lambda *args: FakeOpener())
    with pytest.raises(HTTPException) as caught:
        pagbank.PagBankClient()._request("/orders", payload={}, reference="test")
    assert isinstance(caught.value, pagbank.PixExpirationRejected) is expected


def test_uncertain_network_failure_does_not_allow_replacement(monkeypatch):
    monkeypatch.setenv("PAGBANK_ENVIRONMENT", "sandbox")
    monkeypatch.setenv("PAGBANK_TOKEN", "token-apenas-de-teste")

    class FakeOpener:
        def open(self, request, timeout):
            raise URLError("falha simulada")

    monkeypatch.setattr(pagbank, "build_opener", lambda *args: FakeOpener())
    with pytest.raises(HTTPException) as caught:
        pagbank.PagBankClient()._request("/orders", payload={}, reference="test")
    assert caught.value.status_code == 502
    assert not isinstance(caught.value, pagbank.PixExpirationRejected)
