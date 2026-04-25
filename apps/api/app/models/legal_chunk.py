from datetime import datetime

import uuid
from sqlalchemy import ForeignKey

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class LegalChunk(Base):
    __tablename__ = "legal_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    source_id: Mapped[uuid.UUID] = mapped_column(
    ForeignKey("legal_sources.id", ondelete="CASCADE"),
    nullable=False,
    index=True,
)

    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)

    section_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    citation: Mapped[str] = mapped_column(String(255), nullable=False)
    topic: Mapped[str | None] = mapped_column(String(100), nullable=True)

    text: Mapped[str] = mapped_column(Text, nullable=False)

    embedding: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    source = relationship("LegalSource", back_populates="chunks")