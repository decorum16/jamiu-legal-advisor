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
            .filter(LegalSource.title == "Police Act 2020")
            .first()
        )

        if not source:
            print("Police Act not found")
            return

        deleted = (
            db.query(LegalChunk)
            .filter(LegalChunk.source_id == source.id)
            .delete()
        )

        db.delete(source)
        db.commit()

        print(f"Deleted Police Act and {deleted} chunks")

    finally:
        db.close()


if __name__ == "__main__":
    main()