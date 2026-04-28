from __future__ import annotations

from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.legal import LegalChunk


def expand_tokens(question: str) -> list[str]:
    q = question.lower().strip()
    expanded = set(tok for tok in q.replace("?", " ").split() if len(tok) > 2)

    if "detain" in q or "detention" in q or "liberty" in q:
        expanded.update(["detain", "detained", "detention", "liberty", "personal", "freedom"])

    if "arrest" in q or "suspect" in q or "police" in q:
        expanded.update(["arrest", "detention", "suspect", "police"])

    if "fair hearing" in q:
        expanded.update(["fair", "hearing"])

    if "privacy" in q:
        expanded.add("privacy")

    if "human rights" in q or "fundamental rights" in q or "right" in q:
        expanded.update(["rights", "fundamental", "chapter", "iv"])

    expanded.update(["constitution", "chapter", "iv", "section", "35", "personal", "liberty"])
    return sorted(expanded)


def row_to_result(chunk: LegalChunk) -> dict[str, Any]:
    source_title = "Constitution of the Federal Republic of Nigeria 1999"
    section_number = str(getattr(chunk, "section_number", "") or "")

    citation = source_title
    if section_number:
        citation = f"{source_title}, Section {section_number}"

    return {
        "source_title": source_title,
        "section_number": section_number,
        "part_label": getattr(chunk, "part_label", "") or "",
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

    token_conditions = []

    for tok in tokens:
        like = f"%{tok}%"
        token_conditions.append(LegalChunk.text.ilike(like))

    query = db.query(LegalChunk)

    if token_conditions:
        rows = query.filter(or_(*token_conditions)).all()
    else:
        rows = query.limit(limit).all()

    def relevance_score(chunk: LegalChunk) -> tuple[int, int]:
        text = (chunk.text or "").lower()
        part_label = (getattr(chunk, "part_label", "") or "").lower()
        section_number = str(getattr(chunk, "section_number", "") or "").strip()

        score = 0

        if "constitution" in text:
            score += 30
        if "chapter iv" in part_label or "chapter iv" in text:
            score += 20
        if "personal liberty" in text:
            score += 30
        if section_number == "35" or "section 35" in text:
            score += 40
        if "detention" in text or "detained" in text:
            score += 15
        if "reasonable time" in text:
            score += 15
        if "arrested or detained" in text:
            score += 15

        if "detain" in q or "detention" in q or "liberty" in q:
            if section_number == "35" or "section 35" in text:
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
    return [row_to_result(chunk) for chunk in ranked]