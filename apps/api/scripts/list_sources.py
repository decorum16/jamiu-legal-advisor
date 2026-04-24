from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.db.session import SessionLocal
from app.models.legal import LegalSource


def main():
    db = SessionLocal()
    try:
        rows = db.query(LegalSource).order_by(LegalSource.id.asc()).all()
        for row in rows:
            print(f"id={row.id}, title={row.title}, type={row.source_type}")
    finally:
        db.close()


if __name__ == "__main__":
    main()