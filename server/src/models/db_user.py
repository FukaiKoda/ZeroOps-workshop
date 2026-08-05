"""SQLAlchemy ORM model for authenticated users."""

from datetime import datetime, timezone
from sqlalchemy import Integer, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..core.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # GitHub identity
    github_id: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)
    github_username: Mapped[str] = mapped_column(String(255), nullable=False)
    github_avatar: Mapped[str] = mapped_column(String(512), nullable=True, default="")
    github_email: Mapped[str] = mapped_column(String(255), nullable=True)

    # Stored OAuth token — used for GitHub API calls on behalf of the user.
    # In production this should be encrypted at rest.
    access_token: Mapped[str] = mapped_column(String(512), nullable=False)

    # Progress
    current_level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_xp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    repository: Mapped["Repository"] = relationship(  # noqa: F821
        "Repository", back_populates="user", uselist=False, lazy="selectin"
    )
    submissions: Mapped[list["ExerciseSubmission"]] = relationship(  # noqa: F821
        "ExerciseSubmission", back_populates="user", lazy="selectin"
    )
