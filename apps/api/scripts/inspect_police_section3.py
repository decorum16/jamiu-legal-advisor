from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.db.session import SessionLocal
from app.models.legal import LegalSource, LegalChunk


def main():
    db = SessionLocal()
    try:
        source = (
            db.query(LegalSource)
            .filter(LegalChunk.citation== "Police Act 2020")
            .first()
        )

        if not source:
            print("Police Act 2020 not found")
            return

        rows = (
            db.query(LegalChunk)
            .filter(
                LegalChunk.source_id == source.id,
                LegalChunk.section_number == "3",
            )
            .order_by(LegalChunk.id.asc())
            .all()
        )

        print(f"Found {len(rows)} rows for section 3\n")

        for row in rows:
            print("=" * 80)
            print(f"id         : {row.id}")
            print(f"part_label : {row.part_label}")
            print(f"side_note  : {row.side_note}")
            print("text:")
            print(row.text[:1500])
            print()
    finally:
        db.close()


if __name__ == "__main__":
    main()