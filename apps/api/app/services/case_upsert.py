from __future__ import annotations

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models.case_law import LegalCase, LegalCaseChunk
from app.services.embedding_service import get_text_embedding


def build_chunk_embedding_text(
    case_name: str,
    citation: str | None,
    chunk_type: str | None,
    heading: str | None,
    text: str | None,
) -> str:
    parts: list[str] = []

    if case_name:
        parts.append(f"Case: {case_name}")
    if citation:
        parts.append(f"Citation: {citation}")
    if chunk_type:
        parts.append(f"Chunk type: {chunk_type}")
    if heading:
        parts.append(f"Heading: {heading}")
    if text:
        parts.append(text)

    return "\n".join(parts).strip()


def upsert_case_with_chunks(
    db: Session,
    existing_case: LegalCase | None,
    metadata: dict,
    chunks: list[dict],
) -> tuple[LegalCase, str]:
    if existing_case is None:
        case = LegalCase(
            case_name=metadata["case_name"],
            citation=metadata.get("citation"),
            court=metadata.get("court"),
            court_level=metadata.get("court_level"),
            year=metadata.get("year"),
            subject_area=metadata.get("subject_area"),
            summary=metadata.get("summary"),
        )
        db.add(case)
        db.flush()
        action = "inserted"
    else:
        case = existing_case
        case.case_name = metadata["case_name"]
        case.citation = metadata.get("citation")
        case.court = metadata.get("court")
        case.court_level = metadata.get("court_level")
        case.year = metadata.get("year")
        case.subject_area = metadata.get("subject_area")
        case.summary = metadata.get("summary")

        db.execute(
            delete(LegalCaseChunk).where(LegalCaseChunk.case_id == case.id)
        )
        db.flush()
        action = "updated"

    for chunk in chunks:
        chunk_text = chunk.get("text") or ""
        chunk_type = chunk.get("chunk_type")
        embedding_text = build_chunk_embedding_text(
            case_name=metadata["case_name"],
            citation=metadata.get("citation"),
            chunk_type=chunk_type,
            heading=chunk.get("heading"),
            text=chunk_text,
        )

        embedding = None
        if chunk_type in {"ratio", "holding", "issue"}:
            try:
                embedding = get_text_embedding(embedding_text)
            except Exception:
                embedding = None

        db.add(
            LegalCaseChunk(
                case_id=case.id,
                chunk_type=chunk_type,
                heading=chunk.get("heading"),
                text=chunk_text,
                embedding=embedding,
            )
        )
    db.flush()
    return case, action