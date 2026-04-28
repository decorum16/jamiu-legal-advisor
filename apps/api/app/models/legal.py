from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class LegalChunk(Base):
    __tablename__ = "legal_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

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