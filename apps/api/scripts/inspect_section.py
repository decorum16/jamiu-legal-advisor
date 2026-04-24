from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.db.session import SessionLocal
from app.models.legal import LegalChunk


def main():
    db = SessionLocal()
    try:
        section_number = "3"

        rows = (
            db.query(LegalChunk)
            .filter(LegalChunk.source_id == 3, LegalChunk.section_number == section_number)
            .order_by(LegalChunk.id.asc())
            .all()
        )

        print(f"Found {len(rows)} rows for section {section_number}\n")

        for row in rows:
            print("=" * 80)
            print(f"id          : {row.id}")
            print(f"part_label  : {row.part_label}")
            print(f"section_no  : {row.section_number}")
            print(f"side_note   : {row.side_note}")
            print(f"content_type: {row.content_type}")
            print("text:")
            print(row.text[:1000])
            print()
    finally:
        db.close()


if __name__ == "__main__":
    main()