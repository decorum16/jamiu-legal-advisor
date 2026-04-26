from __future__ import annotations

from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.case_law import LegalCase, LegalCaseChunk


def court_level_weight(court_level: str | None) -> int:
    value = (court_level or "").strip().lower()

    if "supreme" in value:
        return 200
    if "appeal" in value:
        return 140
    if "high" in value:
        return 90
    if "magistrate" in value:
        return 40

    return 20


def chunk_type_weight(chunk_type: str | None) -> int:
    value = (chunk_type or "").strip().lower()

    if value == "ratio":
        return 160
    if value == "holding":
        return 130
    if value == "issue":
        return 80
    if value == "facts":
        return 30

    return 15


def normalize_question(question: str) -> str:
    q = question.strip().lower()

    replacements = [
        "what happens if",
        "can",
        "alone",
        "ground",
        "under nigerian law",
        "in nigeria",
        "what is",
        "what does",
        "say about",
        "please",
        "?",
    ]

    for item in replacements:
        q = q.replace(item, " ")

    return " ".join(q.split())


def expand_tokens(question: str) -> list[str]:
    q = normalize_question(question)
    base_tokens = [tok for tok in q.split() if len(tok) > 2]
    expanded = set(base_tokens)

    q_lower = question.lower()

    if "confession" in q_lower:
        expanded.update([
            "confession",
            "confessional",
            "voluntary",
            "truth",
            "true",
            "direct",
            "positive",
            "unequivocal",
            "admission",
        ])

    if "retracted" in q_lower or "withdrawn" in q_lower:
        expanded.update(["retracted", "retraction", "withdrawn"])

    if "conviction" in q_lower:
        expanded.update(["conviction", "convict"])

    if "detention" in q_lower or "liberty" in q_lower:
        expanded.update(["detention", "detained", "liberty"])

    if "bail" in q_lower:
        expanded.update(["bail"])

    return sorted(expanded)


def doctrine_query_type(question: str) -> str:
    q = question.lower()

    if "confession" in q and "conviction" in q:
        return "confession_conviction"
    if "retracted" in q or "withdrawn" in q:
        return "retracted_confession"
    if "detention" in q or "detain" in q or "liberty" in q:
        return "detention"
    if "bail" in q:
        return "bail"

    return "general"


def _keyword_candidates(
    question: str,
    db: Session,
) -> list[tuple[LegalCaseChunk, LegalCase]]:
    tokens = expand_tokens(question)

    if not tokens:
        return []

    conditions = []

    for tok in tokens:
        like = f"%{tok}%"
        conditions.extend([
            LegalCase.case_name.ilike(like),
            LegalCase.subject_area.ilike(like),
            LegalCase.summary.ilike(like),
            LegalCaseChunk.heading.ilike(like),
            LegalCaseChunk.text.ilike(like),
        ])

    return (
        db.query(LegalCaseChunk, LegalCase)
        .join(LegalCase, LegalCaseChunk.case_id == LegalCase.id)
        .filter(or_(*conditions))
        .all()
    )


def keyword_signal_score(
    tokens: list[str],
    chunk: LegalCaseChunk,
    case: LegalCase,
) -> int:
    text_value = (chunk.text or "").lower()
    heading = (chunk.heading or "").lower()
    summary = (case.summary or "").lower()
    subject_area = (case.subject_area or "").lower()
    case_name = (case.case_name or "").lower()

    score = 0

    for tok in tokens:
        if tok in text_value:
            score += 4
        if tok in heading:
            score += 6
        if tok in summary:
            score += 3
        if tok in subject_area:
            score += 3
        if tok in case_name:
            score += 8

    return score


def doctrine_bonus(
    query_type: str,
    chunk: LegalCaseChunk,
    case: LegalCase,
) -> int:
    text_value = (chunk.text or "").lower()
    chunk_type = (chunk.chunk_type or "").lower()
    source_case_name = (case.case_name or "").lower()
    court_level = (case.court_level or "").lower()

    score = 0

    if query_type == "confession_conviction":
        if "confession" in text_value or "confessional" in text_value:
            score += 20
        if "conviction" in text_value:
            score += 14
        if "voluntary" in text_value:
            score += 10
        if "direct" in text_value and "positive" in text_value:
            score += 14
        if "unequivocal" in text_value:
            score += 10
        if "true" in text_value or "truth" in text_value:
            score += 10
        if chunk_type in {"ratio", "holding"}:
            score += 15

    elif query_type == "retracted_confession":
        if "retracted" in text_value or "withdrawn" in text_value or "retraction" in text_value:
            score += 20
        if "confession" in text_value:
            score += 14
        if "truth" in text_value or "true" in text_value:
            score += 10
        if "surrounding circumstances" in text_value:
            score += 14
        if chunk_type in {"ratio", "holding"}:
            score += 15

    elif query_type == "detention":
        if "detention" in text_value or "liberty" in text_value:
            score += 10

    elif query_type == "bail":
        if "bail" in text_value:
            score += 14

    if chunk_type == "ratio":
        score += 25

    if chunk_type == "holding":
        score += 15

    if "supreme" in court_level and chunk_type in {"ratio", "holding"}:
        score += 25

    if source_case_name:
        score += 2

    return score


def relevance_score(
    question: str,
    tokens: list[str],
    chunk: LegalCaseChunk,
    case: LegalCase,
) -> tuple[float, int, int]:
    query_type = doctrine_query_type(question)

    keyword_score = keyword_signal_score(tokens, chunk, case)
    doctrinal_score = doctrine_bonus(query_type, chunk, case)
    type_score = chunk_type_weight(chunk.chunk_type)
    court_score = court_level_weight(case.court_level)

    year = case.year or 0
    if year >= 2015:
        year_score = 25
    elif year >= 2000:
        year_score = 18
    elif year >= 1980:
        year_score = 10
    else:
        year_score = 5

    total = (
        keyword_score
        + doctrinal_score
        + type_score
        + (court_score * 1.5)
        + year_score
    )

    return (total, court_score, year_score)


def retrieve_case_chunks(
    question: str,
    db: Session,
    limit: int = 5,
) -> list[dict[str, Any]]:
    tokens = expand_tokens(question)

    keyword_rows = _keyword_candidates(question, db)

    ranked_rows = sorted(
        keyword_rows,
        key=lambda row: relevance_score(question, tokens, row[0], row[1]),
        reverse=True,
    )[:limit]

    output: list[dict[str, Any]] = []

    for chunk, case in ranked_rows:
        total_score = relevance_score(question, tokens, chunk, case)[0]
        normalized_score = min(0.99, max(0.50, total_score / 320))

        output.append({
            "case_name": case.case_name,
            "citation": case.citation,
            "court": case.court,
            "court_level": case.court_level,
            "year": case.year,
            "subject_area": case.subject_area,
            "summary": case.summary,
            "chunk_type": chunk.chunk_type,
            "heading": chunk.heading,
            "text": chunk.text,
            "score": round(normalized_score, 3),
        })

    return output