from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.case_law import LegalCase, LegalCaseChunk
from app.services.embedding_service import get_text_embedding


BATCH_SIZE = 50
ALLOWED_CHUNK_TYPES = {"issue", "holding", "ratio"}


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


def fetch_chunks_without_embeddings(db: Session, limit: int) -> list[tuple[LegalCaseChunk, LegalCase]]:
    rows = (
        db.query(LegalCaseChunk, LegalCase)
        .join(LegalCase, LegalCaseChunk.case_id == LegalCase.id)
        .filter(LegalCaseChunk.embedding.is_(None))
        .all()
    )

    filtered: list[tuple[LegalCaseChunk, LegalCase]] = []
    for chunk, case in rows:
        chunk_type = (chunk.chunk_type or "").lower()
        if chunk_type in ALLOWED_CHUNK_TYPES:
            filtered.append((chunk, case))

    return filtered[:limit]


def main() -> None:
    db = SessionLocal()

    processed = 0
    updated = 0
    skipped = 0
    failed = 0

    try:
        while True:
            batch = fetch_chunks_without_embeddings(db, BATCH_SIZE)
            if not batch:
                break

            for chunk, case in batch:
                processed += 1

                try:
                    embedding_text = build_chunk_embedding_text(
                        case_name=case.case_name,
                        citation=case.citation,
                        chunk_type=chunk.chunk_type,
                        heading=chunk.heading,
                        text=chunk.text,
                    )

                    embedding = get_text_embedding(embedding_text)
                    if embedding is None:
                        skipped += 1
                        continue

                    chunk.embedding = embedding
                    updated += 1

                except Exception as exc:
                    failed += 1
                    print(f"Failed chunk_id={chunk.id}: {exc}")

            db.commit()
            print(
                f"Batch committed | processed={processed} updated={updated} "
                f"skipped={skipped} failed={failed}"
            )

        print("Backfill completed.")
        print(f"Processed: {processed}")
        print(f"Updated: {updated}")
        print(f"Skipped: {skipped}")
        print(f"Failed: {failed}")

    finally:
        db.close()


if __name__ == "__main__":
    main()