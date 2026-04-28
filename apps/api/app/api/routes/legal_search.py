import re

from fastapi import APIRouter, Depends
from sqlalchemy import Integer, and_, cast
from sqlalchemy.orm import Session

from app.dependencies.db import get_db
from app.models.legal import LegalChunk
from app.schemas.legal_search import (
    LegalSearchRequest,
    LegalSearchResponse,
    LegalSearchResult,
)

router = APIRouter(prefix="/search", tags=["Legal Search"])


def extract_section_number(query: str) -> str | None:
    match = re.search(r"\b(?:section|sec|s\.)\s*(\d{1,4})\b", query, re.IGNORECASE)
    return match.group(1) if match else None


def normalize_query(query: str) -> str:
    q = query.strip().lower()
    q = re.sub(r"[^\w\s]", " ", q)
    return re.sub(r"\s+", " ", q).strip()


def chunk_to_result(chunk: LegalChunk) -> LegalSearchResult:
    return LegalSearchResult(
        source_title="Statute",
        part_label=getattr(chunk, "part_label", None),
        section_number=str(getattr(chunk, "section_number", "") or ""),
        side_note=getattr(chunk, "side_note", None),
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

    base_query = db.query(LegalChunk)

    if section_query:
        rows = (
            base_query
            .filter(LegalChunk.section_number == section_query)
            .order_by(
                cast(LegalChunk.section_number, Integer).asc(),
                LegalChunk.id.asc(),
            )
            .limit(limit)
            .all()
        )
    else:
        phrase_rows = (
            base_query
            .filter(LegalChunk.text.ilike(f"%{normalized_query}%"))
            .order_by(LegalChunk.id.asc())
            .limit(limit)
            .all()
        )

        if phrase_rows:
            rows = phrase_rows
        else:
            token_conditions = [
                LegalChunk.text.ilike(f"%{tok}%")
                for tok in tokens
            ]

            rows = (
                base_query
                .filter(and_(*token_conditions))
                .order_by(LegalChunk.id.asc())
                .limit(limit)
                .all()
            ) if token_conditions else []

    results = [chunk_to_result(chunk) for chunk in rows]

    return LegalSearchResponse(
        query=query,
        count=len(results),
        results=results,
    )