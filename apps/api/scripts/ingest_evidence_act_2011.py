from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.legal import LegalSource, LegalChunk
from app.services.ingestion.statute_parser import parse_statute_text


SOURCE_TITLE = "Evidence Act 2011"


def main():
    db: Session = SessionLocal()

    try:
        input_path = PROJECT_ROOT / "Legal_sources" / "evidence-act2011-clean.txt"
        raw_text = input_path.read_text(encoding="utf-8")

        chunks = parse_statute_text(raw_text, source_title=SOURCE_TITLE)

        source = LegalSource(
            title=SOURCE_TITLE,
            source_type="statute",
            jurisdiction="Nigeria",
        )
        db.add(source)
        db.commit()
        db.refresh(source)

        print(f"Created source ID: {source.id}")

        count = 0
        seen = set()

        for chunk in chunks:
            if chunk.content_type != "main_section":
                continue

            fingerprint = (
                source.id,
                chunk.part_label,
                chunk.section_number,
                chunk.side_note,
                chunk.text.strip(),
            )
            if fingerprint in seen:
                continue
            seen.add(fingerprint)

            db_chunk = LegalChunk(
                source_id=source.id,
                part_label=chunk.part_label,
                section_number=chunk.section_number,
                side_note=chunk.side_note,
                content_type=chunk.content_type,
                text=chunk.text,
            )
            db.add(db_chunk)
            count += 1

        db.commit()
        print(f"Inserted {count} chunks")

    finally:
        db.close()


if __name__ == "__main__":
    main()