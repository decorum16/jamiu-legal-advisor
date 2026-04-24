import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))

from app.core.database import SessionLocal
from app.services.ingestion_service import LegalIngestionService


def main():
    db = SessionLocal()
    try:
        service = LegalIngestionService(db)

        acja_path = BASE_DIR / "legal_sources" / "acja_2015.txt"
        raw_text = acja_path.read_text(encoding="utf-8")

        document = service.ingest_document(
            title="Administration of Criminal Justice Act 2015",
            short_code="ACJA 2015",
            source_type="statute",
            raw_text=raw_text,
            version_label="2015",
        )

        print(f"Ingested: {document.title}")
    finally:
        db.close()


if __name__ == "__main__":
    main()