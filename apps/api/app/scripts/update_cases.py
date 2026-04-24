from __future__ import annotations

from app.core.database import SessionLocal
from app.services.case_update_pipeline import CaseUpdatePipeline


def normalize_court_level(court: str | None) -> str:
    c = (court or "").lower()

    if "supreme" in c:
        return "supreme"
    if "appeal" in c:
        return "appeal"
    if "high" in c:
        return "high_court"

    return "other"


def load_manual_case_batch() -> list[dict]:
    """
    Replace this later with:
    - file loader
    - API fetcher
    - scraper output
    """
    court = "Supreme Court of Nigeria"

    return [
        {
            "case_name": "Sample Case v State",
            "citation": "(2020) Sample Citation",
            "court": court,
            "court_level": normalize_court_level(court),
            "year": 2020,
            "subject_area": "criminal law",
            "summary": "Sample summary",
            "text": """
Issue for determination: whether the confession was voluntary.

The court held that a confession may ground conviction if it is voluntary and true.

The appeal was dismissed.
""",
        }
    ]


def main() -> None:
    db = SessionLocal()

    try:
        pipeline = CaseUpdatePipeline(db)
        raw_items = load_manual_case_batch()
        report = pipeline.run(raw_items)

        print("Case update completed.")
        print(f"Fetched: {report.fetched}")
        print(f"Inserted: {report.inserted}")
        print(f"Updated: {report.updated}")
        print(f"Skipped: {report.skipped}")
        print(f"Failed: {report.failed}")

        if report.errors:
            print("Errors:")
            for err in report.errors:
                print(f"- {err}")

    finally:
        db.close()


if __name__ == "__main__":
    main()