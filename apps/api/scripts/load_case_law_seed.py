import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.db.session import SessionLocal
from app.models.case_law import LegalCase, LegalCaseChunk


def main() -> None:
    path = Path("data/case_law_seed_criminal.json")
    records = json.loads(path.read_text(encoding="utf-8"))
    print(f"Total records found: {len(records)}")

    db = SessionLocal()

    try:
        inserted_cases = 0
        inserted_chunks = 0

        for record in records:
            existing_case = (
                db.query(LegalCase)
                .filter(LegalCase.case_name == record["case_name"])
                .filter(LegalCase.citation == record.get("citation"))
                .first()
            )

            if existing_case:
                continue

            case = LegalCase(
                case_name=record["case_name"],
                citation=record.get("citation"),
                court=record["court"],
                court_level=record["court_level"],
                year=record.get("year"),
                subject_area=record.get("subject_area"),
                summary=record.get("summary"),
            )
            db.add(case)
            db.flush()

            for chunk in record.get("chunks", []):
                case_chunk = LegalCaseChunk(
                    case_id=case.id,
                    chunk_type=chunk["chunk_type"],
                    heading=chunk.get("heading"),
                    text=chunk["text"],
                )
                db.add(case_chunk)
                inserted_chunks += 1

            inserted_cases += 1

        db.commit()
        print(f"Inserted {inserted_cases} case(s) and {inserted_chunks} chunk(s).")

    finally:
        db.close()


if __name__ == "__main__":
    main()