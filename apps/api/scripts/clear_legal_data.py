from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.db.session import SessionLocal
from app.models.legal import LegalChunk, LegalSource


def main():
    db = SessionLocal()
    try:
        deleted_chunks = db.query(LegalChunk).delete()
        deleted_sources = db.query(LegalSource).delete()
        db.commit()

        print(f"Deleted {deleted_chunks} chunks")
        print(f"Deleted {deleted_sources} sources")
    finally:
        db.close()


if __name__ == "__main__":
    main()