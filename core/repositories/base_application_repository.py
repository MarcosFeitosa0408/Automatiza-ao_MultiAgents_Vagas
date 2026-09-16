from abc import ABC, abstractmethod

from core.schemas.job_application import JobApplicationObject


class BaseJobApplicationRepository(ABC):
    """Define o contrato de persistência para candidaturas."""

    @abstractmethod
    def save(
        self,
        application: JobApplicationObject,
    ) -> JobApplicationObject:
        """Cria ou atualiza uma candidatura."""
        raise NotImplementedError

    @abstractmethod
    def get(
        self,
        application_id: str,
    ) -> JobApplicationObject | None:
        """Busca uma candidatura pelo identificador."""
        raise NotImplementedError

    @abstractmethod
    def list_all(self) -> list[JobApplicationObject]:
        """Retorna todas as candidaturas armazenadas."""
        raise NotImplementedError

    @abstractmethod
    def delete(
        self,
        application_id: str,
    ) -> bool:
        """Remove uma candidatura existente."""
        raise NotImplementedError
