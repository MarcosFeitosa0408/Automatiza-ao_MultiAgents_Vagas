from agents.agent_01_discovery.discovery_agent import DiscoveryAgent
from config.greenhouse_boards import GREENHOUSE_BOARDS


def main():
    """Executa uma descoberta real de vagas nos boards configurados."""

    agent = DiscoveryAgent()

    sources = agent.build_greenhouse_sources(
        GREENHOUSE_BOARDS
    )

    jobs = agent.discover_from_sources(
        sources
    )

    print(f"\nVagas encontradas: {len(jobs)}\n")

    for job in jobs:
        print("-" * 60)
        print(f"Empresa: {job.company}")
        print(f"Cargo: {job.title}")
        print(f"Local: {job.location}")
        print(f"Fonte: {job.source}")
        print(f"URL: {job.url}")


if __name__ == "__main__":
    main()
