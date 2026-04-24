from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from sqlalchemy import func
from app.db.session import SessionLocal
from app.models.legal import LegalChunk


def main():
    db = SessionLocal()
    try:
        rows = (
            db.query(
                LegalChunk.source_id,
                LegalChunk.section_number,
                func.count(LegalChunk.id).label("count"),
            )
            .group_by(LegalChunk.source_id, LegalChunk.section_number)
            .having(func.count(LegalChunk.id) > 1)
            .order_by(func.count(LegalChunk.id).desc(), LegalChunk.section_number.asc())
            .all()
        )

        for row in rows[:30]:
            print(
                f"source_id={row.source_id}, "
                f"section_number={row.section_number}, "
                f"count={row.count}"
            )
    finally:
        db.close()


if __name__ == "__main__":
    main()