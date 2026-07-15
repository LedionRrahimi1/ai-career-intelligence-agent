from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CareerRoadmap(Base):
    __tablename__ = "career_roadmaps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    current_role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    target_role: Mapped[str] = mapped_column(String(255))
    current_skills: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    missing_skills: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    roadmap_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="roadmaps")
