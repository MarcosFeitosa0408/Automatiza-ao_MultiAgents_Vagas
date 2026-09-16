from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from core.models import JobApplicationRecord
from core.repositories.base_job_application_repository import (
    BaseJobApplicationRepository,
)
from core.schemas.job_application import JobApplicationObject


class PostgreSQLJobApplicationRepository(
    BaseJobApplicationRepository
):
    """Persiste candidaturas em PostgreSQL usando SQLAlchemy."""

    def __init__(
        self,
        session_factory: sessionmaker,
    ) -> None:
        self._session_factory = session_factory

    def save(
        self,
        application: JobApplicationObject,
    ) -> JobApplicationObject:
        """Cria ou atualiza uma candidatura persistida."""

        with self._session_factory() as session:
            session: Session

            record = session.get(
                JobApplicationRecord,
                application.application_id,
            )

            payload = application.model_dump(
                mode="json",
            )

            if record is None:
                record = JobApplicationRecord(
                    application_id=application.application_id,
                    payload=payload,
                    created_at=application.created_at,
                    updated_at=application.updated_at,
                )
                session.add(record)
            else:
                record.payload = payload
                record.created_at = application.created_at
                record.updated_at = application.updated_at

            session.commit()

        return application

    def get(
        self,
        application_id: str,
    ) -> JobApplicationObject | None:
        """Busca uma candidatura persistida pelo identificador."""

        with self._session_factory() as session:
            record = session.get(
                JobApplicationRecord,
                application_id,
            )

            if record is None:
                return None

            return JobApplicationObject.model_validate(
                record.payload
            )

    def list_all(self) -> list[JobApplicationObject]:
        """Retorna todas as candidaturas persistidas."""

        with self._session_factory() as session:
            records = session.scalars(
                select(JobApplicationRecord)
            ).all()

            return [
                JobApplicationObject.model_validate(
                    record.payload
                )
                for record in records
            ]

    def delete(
        self,
        application_id: str,
    ) -> bool:
        """Remove uma candidatura persistida."""

        with self._session_factory() as session:
            record = session.get(
                JobApplicationRecord,
                application_id,
            )

            if record is None:
                return False

            session.delete(record)
            session.commit()

            return True
