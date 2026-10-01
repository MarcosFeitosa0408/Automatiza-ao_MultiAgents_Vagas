import httpx
from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def configure_test_credentials(monkeypatch):
    monkeypatch.setenv("ADZUNA_APP_ID", "test-id")
    monkeypatch.setenv("ADZUNA_APP_KEY", "test-key")


def test_search_requires_server_credentials(monkeypatch):
    monkeypatch.delenv("ADZUNA_APP_ID", raising=False)
    monkeypatch.delenv("ADZUNA_APP_KEY", raising=False)

    response = client.post(
        "/opportunities/search",
        json={"query": "Analista de Dados"},
    )

    assert response.status_code == 503
    assert "não foi configurada" in response.json()["detail"]


def test_search_returns_normalized_opportunities(monkeypatch):
    configure_test_credentials(monkeypatch)
    captured = {}

    def fake_fetch(source):
        captured["query"] = source.query
        captured["country"] = source.country
        captured["location"] = source.location

        return [
            {
                "job_id": "test-job",
                "title": "Data Analyst",
                "company": "Empresa de Teste",
                "source": "ADZUNA",
                "url": "https://example.com/job",
                "location": "London",
                "description": "Anúncio usado somente neste teste.",
            }
        ]

    monkeypatch.setattr(
        "core.opportunity_search_api.AdzunaJobSource.fetch_jobs",
        fake_fetch,
    )

    response = client.post(
        "/opportunities/search",
        json={
            "query": " Data Analyst ",
            "country": "GB",
            "location": " London ",
        },
    )

    assert response.status_code == 200
    assert captured == {
        "query": "Data Analyst",
        "country": "gb",
        "location": "London",
    }
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Data Analyst"
    assert response.json()[0]["status"] == "DISCOVERED"


def test_search_rejects_blank_query_and_invalid_country():
    for payload in [
        {"query": "   "},
        {"query": "Dados", "country": "../br"},
    ]:
        response = client.post("/opportunities/search", json=payload)
        assert response.status_code == 422


def test_search_returns_empty_list_when_source_has_no_results(monkeypatch):
    configure_test_credentials(monkeypatch)

    monkeypatch.setattr(
        "core.opportunity_search_api.AdzunaJobSource.fetch_jobs",
        lambda source: [],
    )

    response = client.post(
        "/opportunities/search",
        json={"query": "Analista de Dados"},
    )

    assert response.status_code == 200
    assert response.json() == []


def test_search_handles_timeout_without_exposing_credentials(monkeypatch):
    configure_test_credentials(monkeypatch)

    def fake_fetch(source):
        raise httpx.ReadTimeout("test-key")

    monkeypatch.setattr(
        "core.opportunity_search_api.AdzunaJobSource.fetch_jobs",
        fake_fetch,
    )

    response = client.post(
        "/opportunities/search",
        json={"query": "Analista de Dados"},
    )

    assert response.status_code == 504
    assert "test-key" not in response.text


def test_search_handles_source_failure(monkeypatch):
    configure_test_credentials(monkeypatch)

    def fake_fetch(source):
        raise httpx.ConnectError("Falha de conexão")

    monkeypatch.setattr(
        "core.opportunity_search_api.AdzunaJobSource.fetch_jobs",
        fake_fetch,
    )

    response = client.post(
        "/opportunities/search",
        json={"query": "Analista de Dados"},
    )

    assert response.status_code == 502