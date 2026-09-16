from agents.agent_01_discovery.discovery_agent import DiscoveryAgent
from agents.agent_01_discovery.sources.adzuna_source import AdzunaJobSource
from agents.agent_01_discovery.sources.base_source import BaseJobSource
from agents.agent_01_discovery.sources.greenhouse_source import GreenhouseJobSource
from config.greenhouse_boards import GREENHOUSE_BOARDS
from core.schemas.job import JobOpportunity, WorkModel

def test_discovery_agent_removes_duplicate_jobs():
    jobs = [
        JobOpportunity(
            job_id="vaga-001",
            title="Analista de Dados Júnior",
            company="Empresa A",
            source="TESTE",
            work_model=WorkModel.HYBRID,
        ),
        JobOpportunity(
            job_id="vaga-002",
            title="Analista de BI Júnior",
            company="Empresa B",
            source="TESTE",
            work_model=WorkModel.REMOTE,
        ),
        JobOpportunity(
            job_id="vaga-001",
            title="Analista de Dados Júnior",
            company="Empresa A",
            source="DUPLICADO",
            work_model=WorkModel.HYBRID,
        ),
    ]

    agent = DiscoveryAgent()
    result = agent.discover(jobs)

    assert len(result) == 2
    assert result[0].job_id == "vaga-001"
    assert result[1].job_id == "vaga-002"


def test_discovery_agent_keeps_unique_jobs():
    jobs = [
        JobOpportunity(
            job_id="vaga-010",
            title="Analista de Dados",
            company="Empresa X",
            source="TESTE",
        ),
        JobOpportunity(
            job_id="vaga-011",
            title="Analista de BI",
            company="Empresa Y",
            source="TESTE",
        ),
    ]

    agent = DiscoveryAgent()
    result = agent.discover(jobs)

    assert len(result) == 2


def test_discovery_agent_normalizes_raw_job():
    raw_job = {
        "job_id": "vaga-020",
        "title": "Analista de Dados Júnior",
        "company": "Empresa Teste",
        "source": "TESTE",
        "url": "https://example.com/vagas/020",
        "location": "São Paulo/SP",
        "work_model": "HYBRID",
        "employment_type": "CLT",
        "description": "Atuação com análise de dados e indicadores.",
        "requirements": [
            "Power BI",
            "SQL",
            "Excel",
        ],
        "desirable_requirements": [
            "Python",
        ],
    }

    agent = DiscoveryAgent()

    result = agent.normalize_job(raw_job)

    assert isinstance(result, JobOpportunity)
    assert result.job_id == "vaga-020"
    assert result.title == "Analista de Dados Júnior"
    assert result.company == "Empresa Teste"
    assert result.source == "TESTE"
    assert result.location == "São Paulo/SP"
    assert result.work_model == WorkModel.HYBRID
    assert result.employment_type == "CLT"
    assert result.requirements == [
        "Power BI",
        "SQL",
        "Excel",
    ]
    assert result.desirable_requirements == [
        "Python",
    ]


def test_discovery_agent_normalizes_and_deduplicates_raw_jobs():
    raw_jobs = [
        {
            "job_id": "vaga-030",
            "title": "Analista de Dados Júnior",
            "company": "Empresa A",
            "source": "FONTE_A",
            "work_model": "HYBRID",
        },
        {
            "job_id": "vaga-031",
            "title": "Analista de BI Júnior",
            "company": "Empresa B",
            "source": "FONTE_B",
            "work_model": "REMOTE",
        },
        {
            "job_id": "vaga-030",
            "title": "Analista de Dados Júnior",
            "company": "Empresa A",
            "source": "FONTE_DUPLICADA",
            "work_model": "HYBRID",
        },
    ]

    agent = DiscoveryAgent()

    result = agent.discover_raw(raw_jobs)

    assert len(result) == 2
    assert all(
        isinstance(job, JobOpportunity)
        for job in result
    )
    assert result[0].job_id == "vaga-030"
    assert result[1].job_id == "vaga-031"


def test_discovery_agent_removes_cross_source_duplicates():
    jobs = [
        JobOpportunity(
            job_id="linkedin-123",
            title="Analista de Dados Júnior",
            company="Empresa Alpha",
            source="LINKEDIN",
            location="São Paulo/SP",
            work_model=WorkModel.HYBRID,
        ),
        JobOpportunity(
            job_id="gupy-987",
            title="  analista de dados júnior  ",
            company="EMPRESA ALPHA",
            source="GUPY",
            location="são paulo/sp",
            work_model=WorkModel.HYBRID,
        ),
        JobOpportunity(
            job_id="gupy-988",
            title="Analista de BI Júnior",
            company="Empresa Beta",
            source="GUPY",
            location="São Paulo/SP",
            work_model=WorkModel.REMOTE,
        ),
    ]

    agent = DiscoveryAgent()

    result = agent.discover(jobs)

    assert len(result) == 2
    assert result[0].job_id == "linkedin-123"
    assert result[1].job_id == "gupy-988"


def test_discovery_agent_normalizes_job_with_optional_fields_missing():
    raw_job = {
        "job_id": "vaga-040",
        "title": "Analista de Dados",
        "company": "Empresa Teste",
        "source": "FONTE_TESTE",
    }

    agent = DiscoveryAgent()

    result = agent.normalize_job(raw_job)

    assert result.job_id == "vaga-040"
    assert result.title == "Analista de Dados"
    assert result.company == "Empresa Teste"
    assert result.source == "FONTE_TESTE"
    assert result.location == "NAO_IDENTIFICADO"
    assert result.work_model == WorkModel.UNKNOWN
    assert result.employment_type == "NAO_IDENTIFICADO"
    assert result.description == ""
    assert result.requirements == []
    assert result.desirable_requirements == []


def test_discovery_agent_processes_jobs_from_source():
    class FakeJobSource(BaseJobSource):
        def fetch_jobs(self):
            return [
                {
                    "job_id": "source-001",
                    "title": "Analista de Dados Júnior",
                    "company": "Empresa Source",
                    "source": "FAKE_SOURCE",
                    "work_model": "HYBRID",
                },
                {
                    "job_id": "source-002",
                    "title": "Analista de BI Júnior",
                    "company": "Empresa Source",
                    "source": "FAKE_SOURCE",
                    "work_model": "REMOTE",
                },
            ]

    source = FakeJobSource()
    agent = DiscoveryAgent()

    result = agent.discover_from_source(source)

    assert len(result) == 2
    assert all(
        isinstance(job, JobOpportunity)
        for job in result
    )
    assert result[0].job_id == "source-001"
    assert result[1].job_id == "source-002"


def test_discovery_agent_processes_multiple_sources():
    class SourceA(BaseJobSource):
        def fetch_jobs(self):
            return [
                {
                    "job_id": "source-a-001",
                    "title": "Analista de Dados Júnior",
                    "company": "Empresa Alpha",
                    "source": "SOURCE_A",
                    "location": "São Paulo/SP",
                    "work_model": "HYBRID",
                },
                {
                    "job_id": "source-a-002",
                    "title": "Analista de BI Júnior",
                    "company": "Empresa Beta",
                    "source": "SOURCE_A",
                    "location": "São Paulo/SP",
                    "work_model": "REMOTE",
                },
            ]

    class SourceB(BaseJobSource):
        def fetch_jobs(self):
            return [
                {
                    "job_id": "source-b-900",
                    "title": "  analista de dados júnior  ",
                    "company": "EMPRESA ALPHA",
                    "source": "SOURCE_B",
                    "location": "são paulo/sp",
                    "work_model": "HYBRID",
                },
                {
                    "job_id": "source-b-901",
                    "title": "Analista de Performance",
                    "company": "Empresa Gamma",
                    "source": "SOURCE_B",
                    "location": "São Paulo/SP",
                    "work_model": "HYBRID",
                },
            ]

    agent = DiscoveryAgent()

    result = agent.discover_from_sources(
        [
            SourceA(),
            SourceB(),
        ]
    )

    assert len(result) == 3
    assert all(
        isinstance(job, JobOpportunity)
        for job in result
    )

    job_ids = [
        job.job_id
        for job in result
    ]

    assert "source-a-001" in job_ids
    assert "source-a-002" in job_ids
    assert "source-b-901" in job_ids
    assert "source-b-900" not in job_ids


def test_adzuna_source_converts_api_response_to_raw_jobs():
    api_response = {
        "results": [
            {
                "id": "adzuna-001",
                "title": "Analista de Dados Júnior",
                "company": {
                    "display_name": "Empresa Dados",
                },
                "redirect_url": "https://example.com/vaga/adzuna-001",
                "location": {
                    "display_name": "São Paulo, São Paulo",
                },
                "description": "Atuação com Power BI, SQL e análise de dados.",
            }
        ]
    }

    source = AdzunaJobSource(
        app_id="test-app-id",
        app_key="test-app-key",
    )

    result = source.normalize_response(api_response)

    assert len(result) == 1

    job = result[0]

    assert job["job_id"] == "adzuna-001"
    assert job["title"] == "Analista de Dados Júnior"
    assert job["company"] == "Empresa Dados"
    assert job["source"] == "ADZUNA"
    assert job["url"] == "https://example.com/vaga/adzuna-001"
    assert job["location"] == "São Paulo, São Paulo"
    assert job["description"] == (
        "Atuação com Power BI, SQL e análise de dados."
    )


def test_adzuna_source_fetches_and_normalizes_jobs(monkeypatch):
    api_response = {
        "results": [
            {
                "id": "adzuna-100",
                "title": "Analista de BI Júnior",
                "company": {
                    "display_name": "Empresa Analytics",
                },
                "redirect_url": "https://example.com/vaga/adzuna-100",
                "location": {
                    "display_name": "São Paulo, São Paulo",
                },
                "description": "Vaga para atuação com Power BI e SQL.",
            }
        ]
    }

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return api_response

    def fake_get(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(
        "agents.agent_01_discovery.sources.adzuna_source.httpx.get",
        fake_get,
    )

    source = AdzunaJobSource(
        app_id="test-app-id",
        app_key="test-app-key",
    )

    result = source.fetch_jobs()

    assert len(result) == 1
    assert result[0]["job_id"] == "adzuna-100"
    assert result[0]["title"] == "Analista de BI Júnior"
    assert result[0]["company"] == "Empresa Analytics"
    assert result[0]["source"] == "ADZUNA"


def test_adzuna_source_sends_search_parameters(monkeypatch):
    captured_request = {}

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "results": [],
            }

    def fake_get(url, params, timeout):
        captured_request["url"] = url
        captured_request["params"] = params
        captured_request["timeout"] = timeout

        return FakeResponse()

    monkeypatch.setattr(
        "agents.agent_01_discovery.sources.adzuna_source.httpx.get",
        fake_get,
    )

    source = AdzunaJobSource(
        app_id="test-app-id",
        app_key="test-app-key",
        query="Analista de Dados",
        location="São Paulo",
    )

    result = source.fetch_jobs()

    assert result == []

    assert captured_request["params"]["app_id"] == "test-app-id"
    assert captured_request["params"]["app_key"] == "test-app-key"
    assert captured_request["params"]["what"] == "Analista de Dados"
    assert captured_request["params"]["where"] == "São Paulo"


def test_greenhouse_source_converts_api_response_to_raw_jobs():
    api_response = {
        "jobs": [
            {
                "id": 123456,
                "title": "Data Analyst",
                "location": {
                    "name": "São Paulo, Brazil",
                },
                "absolute_url": "https://example.com/jobs/123456",
                "content": "Atuação com análise de dados, SQL e Power BI.",
            }
        ]
    }

    source = GreenhouseJobSource(
        board_token="empresa-teste",
        company_name="Empresa Teste",
    )

    result = source.normalize_response(api_response)

    assert len(result) == 1

    job = result[0]

    assert job["job_id"] == "greenhouse-123456"
    assert job["title"] == "Data Analyst"
    assert job["company"] == "Empresa Teste"
    assert job["source"] == "GREENHOUSE"
    assert job["url"] == "https://example.com/jobs/123456"
    assert job["location"] == "São Paulo, Brazil"
    assert job["description"] == (
        "Atuação com análise de dados, SQL e Power BI."
    )


def test_greenhouse_source_fetches_and_normalizes_jobs(monkeypatch):
    api_response = {
        "jobs": [
            {
                "id": 789012,
                "title": "Analista de Dados",
                "location": {
                    "name": "São Paulo, Brazil",
                },
                "absolute_url": "https://example.com/jobs/789012",
                "content": "Atuação com SQL, Power BI e indicadores.",
            }
        ]
    }

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return api_response

    def fake_get(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(
        "agents.agent_01_discovery.sources.greenhouse_source.httpx.get",
        fake_get,
    )

    source = GreenhouseJobSource(
        board_token="empresa-teste",
        company_name="Empresa Teste",
    )

    result = source.fetch_jobs()

    assert len(result) == 1
    assert result[0]["job_id"] == "greenhouse-789012"
    assert result[0]["title"] == "Analista de Dados"
    assert result[0]["company"] == "Empresa Teste"
    assert result[0]["source"] == "GREENHOUSE"


def test_greenhouse_boards_create_job_sources():
    sources = [
        GreenhouseJobSource(
            board_token=board["board_token"],
            company_name=board["company_name"],
        )
        for board in GREENHOUSE_BOARDS
    ]

    assert len(sources) >= 1
    assert all(
        isinstance(source, GreenhouseJobSource)
        for source in sources
    )

    bees_source = sources[0]

    assert bees_source.board_token == "bees"
    assert bees_source.company_name == "BEES"


def test_discovery_agent_builds_configured_greenhouse_sources():
    agent = DiscoveryAgent()

    sources = agent.build_greenhouse_sources(
        GREENHOUSE_BOARDS
    )

    assert len(sources) >= 1
    assert all(
        isinstance(source, GreenhouseJobSource)
        for source in sources
    )

    bees_source = sources[0]

    assert bees_source.board_token == "bees"
    assert bees_source.company_name == "BEES"


def test_discovery_agent_discovers_from_configured_greenhouse_boards(
    monkeypatch,
):
    api_response = {
        "jobs": [
            {
                "id": 900001,
                "title": "Analista de Dados",
                "location": {
                    "name": "São Paulo, Brazil",
                },
                "absolute_url": "https://example.com/jobs/900001",
                "content": "Atuação com Power BI, SQL e análise de dados.",
            }
        ]
    }

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return api_response

    def fake_get(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(
        "agents.agent_01_discovery.sources.greenhouse_source.httpx.get",
        fake_get,
    )

    agent = DiscoveryAgent()

    sources = agent.build_greenhouse_sources(
        GREENHOUSE_BOARDS
    )

    result = agent.discover_from_sources(
        sources
    )

    assert len(result) == 1
    assert isinstance(result[0], JobOpportunity)
    assert result[0].job_id == "greenhouse-900001"
    assert result[0].title == "Analista de Dados"
    assert result[0].company == "BEES"
    assert result[0].source == "GREENHOUSE"
    assert result[0].location == "São Paulo, Brazil"
