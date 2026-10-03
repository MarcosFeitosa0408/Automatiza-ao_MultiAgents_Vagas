import json

import pytest

from agents.agent_00_memory.memory_agent import MemoryAgent


@pytest.fixture
def memory_context(tmp_path):
    # Usa a estrutura existente sem alterar o perfil real.
    original = MemoryAgent("tests/fixtures/profile.json").load_profile()
    data = original.model_dump(mode="json")

    data["candidate"]["name"] = "Pessoa de Teste"
    data["candidate"]["career_target"]["primary_roles"] = [
        "Analista de Dados"
    ]
    data["professional_positioning"]["title"] = "Analista de Dados"
    data["skills"]["core"] = ["Power BI"]

    profile_path = tmp_path / "MASTER_PROFILE.json"
    profile_path.write_text(
        json.dumps(data, ensure_ascii=False),
        encoding="utf-8",
    )

    agent = MemoryAgent(profile_path=str(profile_path))
    return agent, data


def test_memory_agent_loads_master_profile(memory_context):
    agent, expected = memory_context

    profile = agent.load_profile()

    assert profile.model_dump(mode="json") == expected


def test_memory_agent_getters(memory_context):
    agent, expected = memory_context

    assert agent.get_candidate_name() == "Pessoa de Teste"
    assert agent.get_primary_roles() == ["Analista de Dados"]
    assert agent.get_core_skills() == ["Power BI"]


def test_memory_agent_reads_updated_profile(memory_context):
    agent, expected = memory_context

    assert agent.get_candidate_name() == "Pessoa de Teste"

    expected["candidate"]["name"] = "Nome Atualizado"
    agent.profile_path.write_text(
        json.dumps(expected, ensure_ascii=False),
        encoding="utf-8",
    )

    assert agent.get_candidate_name() == "Nome Atualizado"