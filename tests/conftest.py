from pathlib import Path
import pytest
from agents.agent_00_memory.memory_agent import MemoryAgent

@pytest.fixture(autouse=True)
def isolate_legacy_tests(request, monkeypatch):
    original_init = MemoryAgent.__init__
    def initialize(self, profile_path='data/master_profile/MASTER_PROFILE.json'):
        if profile_path == 'data/master_profile/MASTER_PROFILE.json':
            profile_path = str(Path(__file__).parent / 'fixtures/profile.json')
        original_init(self, profile_path)
    monkeypatch.setattr(MemoryAgent, '__init__', initialize)
    if request.node.path.name == 'test_account_security.py':
        yield
        return
    if 'api' in request.node.path.parts:
        import main
        from core.auth_api import require_user
        main.app.dependency_overrides[main.get_user_orchestrator] = lambda: main.orchestrator
        main.app.dependency_overrides[require_user] = lambda: {'id': 'test', 'name': 'Teste', 'email': 'test@example.invalid'}
        monkeypatch.setattr(main.orchestrator, 'memory_agent', MemoryAgent())
        yield
        main.app.dependency_overrides.clear()
    else:
        yield
