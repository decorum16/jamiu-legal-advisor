import uuid
from datetime import date

from sqlalchemy import Boolean, Date, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class LegalSource(Base):
    __tablename__ = "legal_sources"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    country: Mapped[str] = mapped_column(String(100), nullable=False, default="Nigeria")
    jurisdiction_level: Mapped[str] = mapped_column(String(50), nullable=False, default="federal")
    state_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_type: Mapped[str] = mapped_column(String(100), nullable=False)
    practice_area: Mapped[str | None] = mapped_column(String(100), nullable=True)
    audience: Mapped[str | None] = mapped_column(String(100), nullable=True)
    citation_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_primary_authority: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    content_text: Mapped[str | None] = mapped_column(Text, nullable=True)