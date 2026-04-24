from __future__ import annotations

from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.legal import LegalChunk, LegalSource


def expand_tokens(question: str) -> list[str]:
    q = question.lower().strip()
    expanded = set(tok for tok in q.replace("?", " ").split() if len(tok) > 2)

    if "detain" in q or "detention" in q:
        expanded.update(["detain", "detained", "detention", "liberty", "personal liberty"])

    if "liberty" in q:
        expanded.update(["liberty", "personal liberty", "freedom"])

    if "arrest" in q or "suspect" in q or "police" in q:
        expanded.update(["arrest", "detention", "suspect", "police"])

    if "fair hearing" in q:
        expanded.update(["fair hearing"])

    if "privacy" in q:
        expanded.update(["privacy"])

    if "human rights" in q or "fundamental rights" in q or "right" in q:
        expanded.update(["rights", "fundamental rights", "chapter iv", "chapter 4"])

    expanded.update(["constitution", "chapter iv", "section 35", "personal liberty"])
    return sorted(expanded)


def row_to_result(chunk: LegalChunk, source: LegalSource) -> dict[str, Any]:
    citation = source.title or "Constitution of the Federal Republic of Nigeria 1999"
    if chunk.section_number is not None:  # type: ignore[comparison-overlap]
        citation = f"{citation}, Section {chunk.section_number}"

    return {
        "source_title": source.title or "Constitution of the Federal Republic of Nigeria 1999",
        "section_number": str(chunk.section_number or ""),
        "part_label": chunk.part_label,
        "citation": citation,
        "text": chunk.text or "",
        "score": 0.95,
    }


def retrieve_constitution_chunks(
    question: str,
    db: Session,
    limit: int = 5,
) -> list[dict[str, Any]]:
    tokens = expand_tokens(question)
    q = question.lower()

    base_query = (
        db.query(LegalChunk, LegalSource)
        .join(LegalSource, LegalChunk.source_id == LegalSource.id)
        .filter(
            or_(
                LegalSource.title.ilike("%constitution%"),
                LegalSource.title.ilike("%cfrn%"),
            )
        )
    )

    token_conditions = []
    for tok in tokens:
        token_conditions.append(
            or_(
                LegalChunk.side_note.ilike(f"%{tok}%"),
                LegalChunk.part_label.ilike(f"%{tok}%"),
                LegalChunk.text.ilike(f"%{tok}%"),
                LegalSource.title.ilike(f"%{tok}%"),
            )
        )

    rows: list[tuple[LegalChunk, LegalSource]] = []
    if token_conditions:
        rows = base_query.filter(or_(*token_conditions)).all()

    def relevance_score(item: tuple[LegalChunk, LegalSource]) -> tuple[int, int]:
        chunk, source = item
        text = (chunk.text or "").lower()
        side_note = (chunk.side_note or "").lower()
        part_label = (chunk.part_label or "").lower()
        source_title = (source.title or "").lower()
        section_number = str(chunk.section_number or "").strip()

        score = 0

        if "constitution" in source_title:
            score += 30
        if "chapter iv" in part_label:
            score += 20
        if "personal liberty" in side_note:
            score += 30
        if section_number == "35":
            score += 40
        if "personal liberty" in text:
            score += 25
        if "detention" in text or "detained" in text:
            score += 15
        if "reasonable time" in text:
            score += 15
        if "within twenty-four hours" in text or "within 24 hours" in text:
            score += 15
        if "arrested or detained" in text:
            score += 15

        if "detain" in q or "detention" in q or "liberty" in q:
            if section_number == "35":
                score += 50
            if "personal liberty" in text:
                score += 25
            if "reasonable time" in text:
                score += 20

        try:
            section_num = int(section_number)
        except Exception:
            section_num = 99999

        return (score, -section_num)

    ranked = sorted(rows, key=relevance_score, reverse=True)[:limit]
    return [row_to_result(chunk, source) for chunk, source in ranked]