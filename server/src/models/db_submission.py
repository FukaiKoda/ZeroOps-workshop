"""SQLAlchemy ORM model for exercise submission history."""

from datetime import datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..core.db import Base


class ExerciseSubmission(Base):
    __tablename__ = "exercise_submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # FK to user
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Exercise reference (matches the folder name, e.g. "ex00_docker_hello_docker")
    exercise_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Result
    # Status: "not_started" | "passed" | "failed"
    status: Mapped[str] = mapped_column(String(20), default="not_started", nullable=False)
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    feedback: Mapped[str] = mapped_column(String(4096), nullable=True, default="")

    # Traceability — links the result to a specific commit
    commit_hash: Mapped[str] = mapped_column(String(40), nullable=True)

    # Timestamp
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationship back to user
    user: Mapped["User"] = relationship("User", back_populates="submissions")  # noqa: F821
