from agents.agent_00_memory.memory_agent import MemoryAgent


def test_memory_agent_loads_master_profile():
    agent = MemoryAgent()
    profile = agent.load_profile()

    assert profile.candidate.name == "Marcos Feitosa"
    assert profile.professional_positioning.title == "Analista de Dados"
    assert len(profile.candidate.career_target.primary_roles) >= 1
    assert len(profile.skills.core) >= 1


def test_memory_agent_getters():
    agent = MemoryAgent()

    assert agent.get_candidate_name() == "Marcos Feitosa"
    assert "Analista de Dados" in agent.get_primary_roles()
    assert "Power BI" in agent.get_core_skills()
