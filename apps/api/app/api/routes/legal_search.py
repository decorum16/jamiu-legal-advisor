import re
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import Integer, and_, cast, or_
from sqlalchemy.orm import Session

from app.dependencies.db import get_db
from app.models.legal import LegalChunk, LegalSource
from app.schemas.legal_search import LegalSearchRequest, LegalSearchResponse, LegalSearchResult

router = APIRouter(prefix="/search", tags=["Legal Search"])


def extract_section_number(query: str) -> str | None:
    match = re.search(r"\b(?:section|sec|s\.)\s*(\d{1,4})\b", query, re.IGNORECASE)
    if match:
        return match.group(1)
    return None


def normalize_query(query: str) -> str:
    q = query.strip().lower()
    q = re.sub(r"[^\w\s]", " ", q)
    q = re.sub(r"\s+", " ", q).strip()
    return q


def chunk_to_result(chunk: LegalChunk, source: LegalSource) -> LegalSearchResult:
    return LegalSearchResult(
        source_title=source.title,
        part_label=chunk.part_label,
        section_number=str(chunk.section_number or ""),
        side_note=chunk.side_note,
        text=chunk.text or "",
    )


@router.post("", response_model=LegalSearchResponse)
def search(
    payload: LegalSearchRequest,
    db: Session = Depends(get_db),
):
    query = payload.query.strip()
    limit = payload.limit

    section_query = extract_section_number(query)
    normalized_query = normalize_query(query)
    tokens = [tok for tok in normalized_query.split() if len(tok) > 2]

    base_query = (
        db.query(LegalChunk, LegalSource)
        .join(LegalSource, LegalChunk.source_id == LegalSource.id)
    )

    if section_query:
        rows = (
            base_query
            .filter(LegalChunk.section_number == section_query)
            .order_by(cast(LegalChunk.section_number, Integer).asc(), LegalChunk.id.asc())
            .limit(limit)
            .all()
        )
    else:
        phrase_rows = (
            base_query
            .filter(
                or_(
                    LegalChunk.side_note.ilike(f"%{normalized_query}%"),
                    LegalChunk.part_label.ilike(f"%{normalized_query}%"),
                    LegalChunk.text.ilike(f"%{normalized_query}%"),
                    LegalChunk.citation.ilike(f"%{normalized_query}%"),
                )
            )
            .order_by(LegalChunk.id.asc())
            .limit(limit)
            .all()
        )

        if phrase_rows:
            rows = phrase_rows
        else:
            token_conditions = []
            for tok in tokens:
                token_conditions.append(
                    or_(
                        LegalChunk.side_note.ilike(f"%{tok}%"),
                        LegalChunk.part_label.ilike(f"%{tok}%"),
                        LegalChunk.text.ilike(f"%{tok}%"),
                        LegalChunk.citation.ilike(f"%{tok}%"),
                    )
                )

            if token_conditions:
                rows = (
                    base_query
                    .filter(and_(*token_conditions))
                    .order_by(LegalChunk.id.asc())
                    .limit(limit)
                    .all()
                )
            else:
                rows = []

    results = [chunk_to_result(chunk, source) for chunk, source in rows]

    return LegalSearchResponse(
        query=query,
        count=len(results),
        results=results,
    )