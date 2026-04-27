from __future__ import annotations

from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.legal import LegalChunk


def expand_tokens(question: str) -> list[str]:
    q = question.lower().strip()
    expanded = set(tok for tok in q.replace("?", " ").split() if len(tok) > 2)

    if "confession" in q:
        expanded.update(["confession", "confessional", "section", "28", "29"])

    if "bail" in q:
        expanded.add("bail")

    if "remand" in q:
        expanded.add("remand")

    if "arrest" in q:
        expanded.add("arrest")

    if "statement" in q:
        expanded.add("statement")

    if "evidence act" in q:
        expanded.update(["evidence", "act"])

    if "police act" in q:
        expanded.update(["police", "act"])

    if "acja" in q or "criminal justice" in q:
        expanded.update(["acja", "administration", "criminal", "justice"])

    return sorted(expanded)


def guess_source_title(chunk: LegalChunk) -> str:
    text = (chunk.text or "").lower()

    if "evidence act" in text or "confession" in text:
        return "Evidence Act"

    if "administration of criminal justice" in text or "acja" in text:
        return "Administration of Criminal Justice Act"

    if "police act" in text or "police" in text:
        return "Police Act"

    return "Statute"


def row_to_result(chunk: LegalChunk) -> dict[str, Any]:
    source_title = guess_source_title(chunk)

    return {
        "source_title": source_title,
        "section_number": "",
        "part_label": "",
        "citation": source_title,
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
        token_conditions.append(LegalChunk.text.ilike(like))

    query = db.query(LegalChunk)

    if token_conditions:
        rows = query.filter(or_(*token_conditions)).all()
    else:
        rows = query.limit(limit).all()

    def relevance_score(chunk: LegalChunk) -> int:
        text = (chunk.text or "").lower()
        source_title = guess_source_title(chunk).lower()

        score = statute_source_boost(source_title)

        for tok in tokens:
            if tok in text:
                score += 5

        if "confession" in q:
            if "evidence act" in source_title:
                score += 40
            if "section 28" in text or "28." in text:
                score += 30
            if "section 29" in text or "29." in text:
                score += 20
            if "confession" in text or "confessional" in text:
                score += 25

        if "bail" in q and (
            "acja" in source_title or "criminal justice" in source_title
        ):
            score += 20

        if "police" in q and "police act" in source_title:
            score += 20

        return score

    ranked = sorted(rows, key=relevance_score, reverse=True)[:limit]
    return [row_to_result(chunk) for chunk in ranked]
