from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class OldLegalChunk(Base):
    __tablename__ = "legal_chunks"

id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

document_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)

part_label: Mapped[str | None] = mapped_column(String(100), nullable=True)

section_number: Mapped[str | None] = mapped_column(String(50), nullable=True)

side_note: Mapped[str | None] = mapped_column(String(255), nullable=True)

text: Mapped[str] = mapped_column(Text, nullable=False)

embedding: Mapped[str | None] = mapped_column(Text, nullable=True)

created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    