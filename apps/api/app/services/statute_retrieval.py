from __future__ import annotations

from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.legal import LegalChunk


def expand_tokens(question: str) -> list[str]:
    q = question.lower().strip()
    expanded = set(tok for tok in q.replace("?", " ").split() if len(tok) > 2)

    if "confession" in q:
        expanded.update(["confession", "confessional", "section 28", "section 29"])

    if "bail" in q:
        expanded.add("bail")

    if "remand" in q:
        expanded.add("remand")

    if "arrest" in q:
        expanded.add("arrest")

    if "statement" in q:
        expanded.add("statement")

    if "evidence act" in q:
        expanded.update(["evidence", "evidence act"])

    if "police act" in q:
        expanded.update(["police", "police act"])

    if "acja" in q or "criminal justice" in q:
        expanded.update(["acja", "administration", "criminal", "justice"])

    return sorted(expanded)


def guess_source_title(chunk: LegalChunk) -> str:
    citation = (chunk.citation or "").lower()
    text = (chunk.text or "").lower()
    combined = f"{citation} {text}"

    if "evidence act" in combined or "confession" in combined:
        return "Evidence Act"

    if "administration of criminal justice" in combined or "acja" in combined:
        return "Administration of Criminal Justice Act"

    if "police act" in combined or "police" in combined:
        return "Police Act"

    return "Statute"


def row_to_result(chunk: LegalChunk) -> dict[str, Any]:
    source_title = guess_source_title(chunk)

    citation = chunk.citation or source_title
    if getattr(chunk, "section_number", None):
        citation = f"{source_title}, Section {chunk.section_number}"

    return {
        "source_title": source_title,
        "section_number": str(getattr(chunk, "section_number", "") or ""),
        "part_label": getattr(chunk, "part_label", None),
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

    token_conditions = []

    for tok in tokens:
        like = f"%{tok}%"
        token_conditions.append(
            or_(
                LegalChunk.side_note.ilike(like),
                LegalChunk.part_label.ilike(like),
                LegalChunk.text.ilike(like),
                LegalChunk.citation.ilike(like),
            )
        )

    query = db.query(LegalChunk)

    if token_conditions:
        rows = query.filter(or_(*token_conditions)).all()
    else:
        rows = query.limit(limit).all()

    def relevance_score(chunk: LegalChunk) -> tuple[int, int]:
        text = (chunk.text or "").lower()
        side_note = (getattr(chunk, "side_note", None) or "").lower()
        part_label = (getattr(chunk, "part_label", None) or "").lower()
        citation = (chunk.citation or "").lower()
        source_title = guess_source_title(chunk).lower()
        section_number = str(getattr(chunk, "section_number", "") or "").strip()

        score = statute_source_boost(source_title)

        for tok in tokens:
            if tok in text:
                score += 4
            if tok in side_note:
                score += 6
            if tok in part_label:
                score += 5
            if tok in citation:
                score += 8
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

        if "bail" in q and (
            "acja" in source_title or "criminal justice" in source_title
        ):
            score += 20

        if "police" in q and "police act" in source_title:
            score += 20

        try:
            section_num = int(section_number)
        except Exception:
            section_num = 99999

        return (score, -section_num)

    ranked = sorted(rows, key=relevance_score, reverse=True)[:limit]
    return [row_to_result(chunk) for chunk in ranked]