from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class LegalDocument(Base):
    __tablename__ = "legal_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    short_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    jurisdiction: Mapped[str] = mapped_column(String(100), nullable=False, default="Nigeria")
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    version_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    chunks = relationship("LegalChunk", back_populates="document", cascade="all, delete-orphan")
    