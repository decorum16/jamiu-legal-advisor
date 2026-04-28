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
            .filter(LegalChunk.citation == "Police Act 2020")
            .first()
        )

        if not source:
            print("Police Act 2020 not found")
            return

        rows = (
            db.query(LegalChunk.part_label)
            .filter(LegalChunk. == source.id)
            .distinct()
            .all()
        )

        for row in rows[:20]:
            print(row[0])
    finally:
        db.close()


if __name__ == "__main__":
    main()