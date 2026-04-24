from __future__ import annotations

from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.legal import LegalChunk, LegalSource


def expand_tokens(question: str) -> list[str]:
    q = question.lower().strip()
    expanded = set(tok for tok in q.replace("?", " ").split() if len(tok) > 2)

    if "confession" in q:
        expanded.update(["confession", "confessional", "section 28", "section 29"])

    if "bail" in q:
        expanded.update(["bail"])

    if "remand" in q:
        expanded.update(["remand"])

    if "arrest" in q:
        expanded.update(["arrest"])

    if "statement" in q:
        expanded.update(["statement"])

    if "evidence act" in q:
        expanded.update(["evidence act"])

    if "police act" in q:
        expanded.update(["police act"])

    if "acja" in q or "criminal justice" in q:
        expanded.update(["acja", "administration of criminal justice"])

    return sorted(expanded)


def row_to_result(chunk: LegalChunk, source: LegalSource) -> dict[str, Any]:
    citation = source.title or "Statute"
    if chunk.section_number:
        citation = f"{citation}, Section {chunk.section_number}"

    return {
        "source_title": source.title or "Statute",
        "section_number": str(chunk.section_number or ""),
        "part_label": chunk.part_label,
        "citation": citation,
        "text": chunk.text or "",
        "score": 0.90,
    }


def statute_source_boost(source_title: str) -> int:
    title = (source_title or "").lower()

    if "evidence act" in title:
        return 100
    if "administration of criminal justice" in title or "acja" in title:
        return 95
    if "police act" in title:
        return 90
    return 50


def retrieve_statute_chunks(
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
                LegalSource.title.ilike("%act%"),
                LegalSource.title.ilike("%acja%"),
                LegalSource.title.ilike("%evidence%"),
                LegalSource.title.ilike("%police%"),
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
        source_title = (source.title or "").lower()
        section_number = str(chunk.section_number or "").strip()

        score = statute_source_boost(source.title or "")

        for tok in tokens:
            if tok in text:
                score += 4
            if tok in side_note:
                score += 6
            if tok in source_title:
                score += 8

        if "confession" in q:
            if "evidence act" in source_title:
                score += 40
            if section_number == "28":
                score += 30
            if section_number == "29":
                score += 20
            if "confession" in text or "confession" in side_note:
                score += 20

        if "bail" in q and ("acja" in source_title or "criminal justice" in source_title):
            score += 20

        if "police" in q and "police act" in source_title:
            score += 20

        try:
            section_num = int(section_number)
        except Exception:
            section_num = 99999

        return (score, -section_num)

    ranked = sorted(rows, key=relevance_score, reverse=True)[:limit]
    return [row_to_result(chunk, source) for chunk, source in ranked]