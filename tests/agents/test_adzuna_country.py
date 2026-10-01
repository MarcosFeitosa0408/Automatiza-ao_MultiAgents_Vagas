import pytest

from agents.agent_01_discovery.sources.adzuna_source import AdzunaJobSource


@pytest.mark.parametrize(
    ("country", "expected"),
    [
        ("br", "br"),
        (" GB ", "gb"),
        ("us", "us"),
    ],
)
def test_adzuna_uses_selected_country(monkeypatch, country, expected):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"results": []}

    def fake_get(url, params, timeout):
        captured["url"] = url
        captured["params"] = params
        return FakeResponse()

    monkeypatch.setattr(
        "agents.agent_01_discovery.sources.adzuna_source.httpx.get",
        fake_get,
    )

    source = AdzunaJobSource(
        app_id="test-id",
        app_key="test-key",
        query="Data Analyst",
        location="London",
        country=country,
    )

    assert source.fetch_jobs() == []
    assert captured["url"] == (
        f"https://api.adzuna.com/v1/api/jobs/{expected}/search/1"
    )
    assert captured["params"]["what"] == "Data Analyst"
    assert captured["params"]["where"] == "London"


def test_adzuna_preserves_brazil_as_default():
    source = AdzunaJobSource(app_id="test-id", app_key="test-key")

    assert source.country == "br"


@pytest.mark.parametrize("country", ["", "Brasil", "../br", "12", "éé"])
def test_adzuna_rejects_invalid_country_format(country):
    with pytest.raises(ValueError, match="duas letras"):
        AdzunaJobSource(
            app_id="test-id",
            app_key="test-key",
            country=country,
        )