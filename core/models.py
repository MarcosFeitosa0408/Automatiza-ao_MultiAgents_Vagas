from datetime import datetime

from sqlalchemy import DateTime, JSON, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base declarativa dos modelos SQLAlchemy."""


class JobApplicationRecord(Base):
    """Representação persistente de uma candidatura."""

    __tablename__ = "job_applications"

    application_id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )

    payload: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
