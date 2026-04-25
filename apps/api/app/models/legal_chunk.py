from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class LegalChunk(Base):
    __tablename__ = "legal_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    document_id: Mapped[int] = mapped_column(
        ForeignKey("legal_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)

    section_label: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True
    )

    citation: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )

    topic: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True
    )

    text: Mapped[str] = mapped_column(Text, nullable=False)

    # 🔥 TEMP FIX: remove pgvector dependency
    embedding: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    document = relationship("LegalDocument", back_populates="chunks")