from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class LegalChunk(Base):
    __tablename__ = "legal_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # ✅ THIS IS THE FIX
    document_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("legal_documents.id"),
        nullable=False,
        index=True,
    )

    chunk_index: Mapped[int] = mapped_column(Integer, nullable=True)

    part_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    section_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    side_note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    citation: Mapped[str | None] = mapped_column(String(255), nullable=True)

    text: Mapped[str] = mapped_column(Text, nullable=False)

    embedding: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ✅ relationship restored
    document = relationship("LegalDocument", back_populates="chunks")