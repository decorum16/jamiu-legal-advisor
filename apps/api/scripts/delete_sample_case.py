import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.db.session import SessionLocal
from app.models.case_law import LegalCase, LegalCaseChunk


SAMPLE_CASE_NAME = "Sample Case v Sample State"


def main() -> None:
    db = SessionLocal()

    try:
        case = (
            db.query(LegalCase)
            .filter(LegalCase.case_name == SAMPLE_CASE_NAME)
            .first()
        )

        if not case:
            print("Sample case not found.")
            return

        deleted_chunks = (
            db.query(LegalCaseChunk)
            .filter(LegalCaseChunk.case_id == case.id)
            .delete()
        )

        db.delete(case)
        db.commit()

        print(f"Deleted sample case and {deleted_chunks} related chunk(s).")

    finally:
        db.close()


if __name__ == "__main__":
    main()