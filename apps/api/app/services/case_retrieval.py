from __future__ import annotations

from typing import Any

from sqlalchemy import or_, text
from sqlalchemy.orm import Session

from app.models.case_law import LegalCase, LegalCaseChunk
from app.services.embedding_service import get_text_embedding

def court_level_weight(court_level: str | None) -> int:
    value = (court_level or "").strip().lower()

    # Supreme Court (final authority)
    if "supreme" in value:
        return 200

    # Court of Appeal
    if "appeal" in value:
        return 140

    # High Court (Federal/State)
    if "high" in value:
        return 90

    # Magistrate / others
    if "magistrate" in value:
        return 40

    return 20

def chunk_type_weight(chunk_type: str | None) -> int:
    value = (chunk_type or "").strip().lower()

    # Ratio decidendi (binding law)
    if value == "ratio":
        return 160

    # Holding (strong but slightly below ratio)
    if value == "holding":
        return 130

    # Issue framing
    if value == "issue":
        return 80

    # Facts (weak for doctrine)
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
        expanded.update(
            [
                "confession",
                "confessional",
                "voluntary",
                "truth",
                "true",
                "direct",
                "positive",
                "unequivocal",
                "admission",
            ]
        )

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

    rows = (
        db.query(LegalCaseChunk, LegalCase)
        .join(LegalCase, LegalCaseChunk.case_id == LegalCase.id)
        .filter(
            or_(
                *[LegalCase.case_name.ilike(f"%{tok}%") for tok in tokens],
                *[LegalCase.subject_area.ilike(f"%{tok}%") for tok in tokens],
                *[LegalCase.summary.ilike(f"%{tok}%") for tok in tokens],
                *[LegalCaseChunk.heading.ilike(f"%{tok}%") for tok in tokens],
                *[LegalCaseChunk.text.ilike(f"%{tok}%") for tok in tokens],
            )
        )
        .all()
    )

    return rows


def _vector_candidates(
    question: str,
    db: Session,
    limit: int = 12,
) -> list[tuple[LegalCaseChunk, LegalCase, float]]:
    embedding = get_text_embedding(question)
    if not embedding:
        return []

    sql = text(
        """
        SELECT
            c.id AS chunk_id,
            c.case_id AS case_id,
            c.embedding <=> CAST(:embedding AS vector) AS distance
        FROM legal_case_chunks c
        WHERE c.embedding IS NOT NULL
          AND c.chunk_type IN ('issue', 'holding', 'ratio')
        ORDER BY c.embedding <=> CAST(:embedding AS vector)
        LIMIT :limit
        """
    )

    embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"

    rows = db.execute(
        sql,
        {
            "embedding": embedding_str,
            "limit": limit,
        },
    ).mappings().all()

    if not rows:
        return []

    chunk_ids = [row["chunk_id"] for row in rows]
    id_to_distance = {row["chunk_id"]: float(row["distance"]) for row in rows}

    orm_rows = (
        db.query(LegalCaseChunk, LegalCase)
        .join(LegalCase, LegalCaseChunk.case_id == LegalCase.id)
        .filter(LegalCaseChunk.id.in_(chunk_ids))
        .all()
    )

    output: list[tuple[LegalCaseChunk, LegalCase, float]] = []
    for chunk, case in orm_rows:
        output.append((chunk, case, id_to_distance.get(chunk.id, 1.0)))

    return output


def semantic_score_from_distance(distance: float | None) -> int:
    if distance is None:
        return 0

    if distance <= 0.15:
        return 120
    if distance <= 0.25:
        return 100
    if distance <= 0.35:
        return 80
    if distance <= 0.45:
        return 60
    if distance <= 0.60:
        return 35
    return 10


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
    q: str,
    chunk: LegalCaseChunk,
    case: LegalCase,
) -> int:
    text_value = (chunk.text or "").lower()
    heading = (chunk.heading or "").lower()
    source_case_name = (case.case_name or "").lower()
    chunk_type = (chunk.chunk_type or "").lower()

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

      # Strong preference for ratio decidendi
        if chunk_type == "ratio":
           score += 25

    # Secondary preference for holding
        if chunk_type == "holding":
           score += 15

    if source_case_name:
        score += 2
  # Extra boost for Supreme Court doctrinal statements
    if case.court_level == "supreme" and chunk.chunk_type in {"ratio", "holding"}:
     score += 25
    return score


def relevance_score(
    question: str,
    tokens: list[str],
    item: dict[str, Any],
) -> tuple[float, int, int]:
    q = question.lower()
    query_type = doctrine_query_type(question)

    chunk: LegalCaseChunk = item["chunk"]
    case: LegalCase = item["case"]
    keyword_hit: bool = item["keyword_hit"]
    vector_distance = item["vector_distance"]

    semantic_score = semantic_score_from_distance(vector_distance)
    keyword_score = keyword_signal_score(tokens, chunk, case)
    doctrinal_score = doctrine_bonus(query_type, q, chunk, case)
    type_score = chunk_type_weight(chunk.chunk_type)
    court_score = court_level_weight(case.court_level)
    
    year = case.year or 0

    # Recency weighting (modern cases slightly preferred)
    if year >= 2015:
            year_score = 25
    elif year >= 2000:
            year_score = 18
    elif year >= 1980:
            year_score = 10
    else:
            year_score = 5

    if keyword_hit:
        keyword_score += 15

    total = (
        semantic_score
        + keyword_score
        + doctrinal_score
        + type_score
        + (court_score * 1.5)
        + year_score   # ← NEW
    )

    return (total, court_score, year_score)


def retrieve_case_chunks(
    question: str,
    db: Session,
    limit: int = 5,
) -> list[dict[str, Any]]:
    tokens = expand_tokens(question)

    keyword_rows = _keyword_candidates(question, db)
    vector_rows = _vector_candidates(question, db, limit=max(10, limit * 4))

    merged: dict[int, dict[str, Any]] = {}

    for chunk, case in keyword_rows:
        merged[chunk.id] = {
            "chunk": chunk,
            "case": case,
            "keyword_hit": True,
            "vector_distance": None,
        }

    for chunk, case, distance in vector_rows:
        if chunk.id in merged:
            merged[chunk.id]["vector_distance"] = distance
        else:
            merged[chunk.id] = {
                "chunk": chunk,
                "case": case,
                "keyword_hit": False,
                "vector_distance": distance,
            }

    items = list(merged.values())
    ranked = sorted(
        items,
        key=lambda item: relevance_score(question, tokens, item),
        reverse=True,
    )[:limit]

    output: list[dict[str, Any]] = []
    for item in ranked:
        chunk: LegalCaseChunk = item["chunk"]
        case: LegalCase = item["case"]

        total_score = relevance_score(question, tokens, item)[0]
        normalized_score = min(0.99, max(0.50, total_score / 320))

        output.append(
            {
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
            }
        )

    return output