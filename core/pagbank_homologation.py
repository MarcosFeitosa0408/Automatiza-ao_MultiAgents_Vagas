"""Captura temporaria e opcional para homologacao; nunca inclui headers."""
import json
import logging
import os
import re
import uuid
from datetime import datetime, timezone

PREFIX = "PAGBANK_HOMOLOGACAO "
LOGGER = logging.getLogger(__name__)
PRIVATE = {
    "name", "email", "taxid", "cpf", "cnpj", "phone", "phones",
    "telephone", "address", "shipping", "holder", "card", "number",
    "authorization", "token", "accesstoken", "refreshtoken", "secret",
    "clientsecret", "apikey", "password", "senha", "cookie", "setcookie",
    "qrtext", "qrcode", "links", "href", "notificationurls",
}


def redact(value, token):
    if isinstance(value, dict):
        return {
            key: "[OCULTO]" if re.sub(r"[^a-z0-9]", "", key.lower()) in PRIVATE
            else redact(item, token)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item, token) for item in value]
    if isinstance(value, str):
        if token:
            value = value.replace(token, "[OCULTO]")
        value = re.sub(r"(?i)Bearer\s+[^\s\"<>]+", "Bearer [OCULTO]", value)
        return value
    return value


def emit(record, token):
    # A captura nunca deve alterar o resultado de uma operacao financeira.
    try:
        safe = redact(record, token)
        line = json.dumps(safe, ensure_ascii=True, separators=(",", ":"))
        if len(line) > 60000:
            LOGGER.warning("PagBank: registro de homologacao omitido por tamanho.")
            return
        LOGGER.warning("%s%s", PREFIX, line)
    except Exception:
        LOGGER.warning("PagBank: nao foi possivel registrar a homologacao.")


def begin_capture(environment, path, payload, reference, token):
    if os.getenv("PAGBANK_HOMOLOGATION_LOG_ENABLED", "").strip().lower() != "true":
        return None
    record = {
        "capture_id": uuid.uuid4().hex,
        "environment": environment,
        "method": "POST" if payload is not None else "GET",
        "path": path,
        "reference": reference,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "personal_data_redacted": True,
        "event": "request",
        "request_body": payload,
    }
    emit(record, token)
    return record["capture_id"]


def end_capture(capture_id, *, token, http_status=None, response=None, error_type=None):
    if capture_id is None:
        return
    emit({
        "capture_id": capture_id,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "event": "response" if error_type is None else "error",
        "http_status": http_status,
        "response_body": response,
        "error_type": error_type,
    }, token)
