import pytest
from fastapi.testclient import TestClient

import main
from agents.agent_00_memory.memory_agent import MemoryAgent


@pytest.fixture
def profile_context(tmp_path, monkeypatch):
    # Lê o perfil existente, mas salva apenas na pasta temporária.
    profile = MemoryAgent("tests/fixtures/profile.json").load_profile()
    profile_path = tmp_path / "MASTER_PROFILE.json"
    agent = MemoryAgent(profile_path=str(profile_path))
    agent.save_profile(profile)

    monkeypatch.setattr(main.orchestrator, "memory_agent", agent)

    with TestClient(main.app) as client:
        yield client, agent, profile


def test_get_profile_returns_saved_data(profile_context):
    client, agent, profile = profile_context

    response = client.get("/profile")

    assert response.status_code == 200
    assert response.json() == profile.model_dump(mode="json")


def test_update_profile_persists_and_refreshes_agent(profile_context):
    client, agent, profile = profile_context
    payload = profile.model_dump(mode="json")
    payload["candidate"]["name"] = "Pessoa de Teste"
    payload["skills"]["core"] = ["SQL", "Power BI"]

    response = client.put("/profile", json=payload)

    assert response.status_code == 200
    assert response.json()["candidate"]["name"] == "Pessoa de Teste"

    # Confirma leitura pelo agente já usado pelo orquestrador.
    assert agent.get_candidate_name() == "Pessoa de Teste"
    assert agent.get_core_skills() == ["SQL", "Power BI"]

    # Confirma persistência em uma nova instância.
    reloaded = MemoryAgent(profile_path=str(agent.profile_path))
    assert reloaded.get_candidate_name() == "Pessoa de Teste"


def test_invalid_profile_preserves_saved_file(profile_context):
    client, agent, profile = profile_context
    previous_content = agent.profile_path.read_bytes()
    payload = profile.model_dump(mode="json")
    payload["unexpected_field"] = "Não permitido"

    response = client.put("/profile", json=payload)

    assert response.status_code == 422
    assert agent.profile_path.read_bytes() == previous_content


def test_missing_profile_returns_404(profile_context):
    client, agent, profile = profile_context
    agent.profile_path.unlink()

    response = client.get("/profile")

    assert response.status_code == 404


def test_write_failure_preserves_saved_file(profile_context, monkeypatch):
    client, agent, profile = profile_context
    previous_content = agent.profile_path.read_bytes()
    payload = profile.model_dump(mode="json")
    payload["candidate"]["name"] = "Alteração não salva"

    def fail_replace(*args, **kwargs):
        raise OSError("Falha simulada de gravação")

    monkeypatch.setattr(
        "agents.agent_00_memory.memory_agent.os.replace",
        fail_replace,
    )

    response = client.put("/profile", json=payload)

    assert response.status_code == 500
    assert agent.profile_path.read_bytes() == previous_content
    assert list(agent.profile_path.parent.glob("*.tmp")) == []