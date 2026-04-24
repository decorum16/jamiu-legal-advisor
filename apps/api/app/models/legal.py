from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class LegalSource(Base):
    __tablename__ = "legal_sources"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    source_type = Column(String, nullable=False)
    jurisdiction = Column(String, default="Nigeria")

    chunks = relationship("LegalChunk", back_populates="source")


class LegalChunk(Base):
    __tablename__ = "legal_chunks"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("legal_sources.id"))

    part_label = Column(String, nullable=True)
    section_number = Column(String, nullable=True)
    side_note = Column(String, nullable=True)
    content_type = Column(String, default="main_section")
    text = Column(Text, nullable=False)

    source = relationship("LegalSource", back_populates="chunks")