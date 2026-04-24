import json
import sys
from pathlib import Path

# Make the project root importable when running this file directly:
# python scripts/load_constitution_chapter_iv.py
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.db.session import SessionLocal
from app.models.legal import LegalChunk, LegalSource


SOURCE_TITLE = "Constitution of the Federal Republic of Nigeria 1999"


def get_or_create_source(db):
    source = db.query(LegalSource).filter(LegalSource.title == SOURCE_TITLE).first()
    if source:
        return source

    source = LegalSource(
    title=SOURCE_TITLE,
    source_type="constitution",
    jurisdiction="federal",
)
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


def main() -> None:
    path = Path("constitution_chapter_iv_parsed.json")
    records = json.loads(path.read_text(encoding="utf-8"))

    db = SessionLocal()

    try:
        source = get_or_create_source(db)
        inserted = 0

        for record in records:
            exists = (
                db.query(LegalChunk)
                .filter(LegalChunk.source_id == source.id)
                .filter(LegalChunk.section_number == record["section_number"])
                .first()
            )
            if exists:
                continue

            chunk = LegalChunk(
                source_id=source.id,
                part_label=record.get("part_label"),
                section_number=record.get("section_number"),
                side_note=record.get("side_note"),
                text=record.get("text", ""),
            )
            db.add(chunk)
            inserted += 1

        db.commit()
        print(f"Inserted {inserted} constitutional sections.")

    finally:
        db.close()


if __name__ == "__main__":
    main()