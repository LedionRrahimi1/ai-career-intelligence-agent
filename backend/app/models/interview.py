from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    interview_type: Mapped[str] = mapped_column(String(64))
    questions: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    answers: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    overall_score: Mapped[float | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="interview_sessions")
