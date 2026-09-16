from core.repositories.base_job_application_repository import (
    BaseJobApplicationRepository,
)
from core.schemas.job_application import JobApplicationObject


class InMemoryJobApplicationRepository(
    BaseJobApplicationRepository
):
    """Armazena candidaturas em memória durante a execução da aplicação."""

    def __init__(self) -> None:
        self._applications: dict[str, JobApplicationObject] = {}

    def save(
        self,
        application: JobApplicationObject,
    ) -> JobApplicationObject:
        """Cria ou atualiza uma candidatura."""

        self._applications[application.application_id] = application
        return application

    def get(
        self,
        application_id: str,
    ) -> JobApplicationObject | None:
        """Busca uma candidatura pelo identificador."""

        return self._applications.get(application_id)

    def list_all(self) -> list[JobApplicationObject]:
        """Retorna todas as candidaturas armazenadas."""

        return list(self._applications.values())

    def delete(
        self,
        application_id: str,
    ) -> bool:
        """Remove uma candidatura existente."""

        if application_id not in self._applications:
            return False

        del self._applications[application_id]
        return True
