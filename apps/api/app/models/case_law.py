from sqlalchemy import ForeignKey, String, Text, Integer
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db.base import Base


class LegalCase(Base):
    __tablename__ = "legal_cases"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    case_name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    citation: Mapped[str | None] = mapped_column(String(255), nullable=True)
    court: Mapped[str | None] = mapped_column(String(255), nullable=True)
    court_level: Mapped[str | None] = mapped_column(String(100), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    subject_area: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    chunks: Mapped[list["LegalCaseChunk"]] = relationship(
        "LegalCaseChunk",
        back_populates="case",
        cascade="all, delete-orphan",
    )


class LegalCaseChunk(Base):
    __tablename__ = "legal_case_chunks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    case_id: Mapped[int] = mapped_column(
        ForeignKey("legal_cases.id"),
        nullable=False,
        index=True,
    )
    chunk_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    heading: Mapped[str | None] = mapped_column(String(255), nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    # Temporarily stored as text until pgvector is properly enabled
    embedding: Mapped[str | None] = mapped_column(Text, nullable=True)

    case = relationship("LegalCase", back_populates="chunks")