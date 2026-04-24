from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.legal_chunk import LegalChunk


class RAGService:
    def __init__(self, db: Session):
        self.db = db

    def keyword_search(self, query: str, limit: int = 5):
        stmt = (
            select(LegalChunk)
            .where(
                or_(
                    LegalChunk.text.ilike(f"%{query}%"),
                    LegalChunk.citation.ilike(f"%{query}%"),
                    LegalChunk.section_label.ilike(f"%{query}%"),
                    LegalChunk.topic.ilike(f"%{query}%"),
                )
            )
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())