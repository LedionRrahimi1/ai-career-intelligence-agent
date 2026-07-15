from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CV(Base):
    __tablename__ = "cvs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    file_url: Mapped[str] = mapped_column(String(512))
    original_filename: Mapped[str] = mapped_column(String(255))
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    profile_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # serialized candidate profile
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="cvs")
    analyses = relationship("Analysis", back_populates="cv", cascade="all, delete-orphan")
