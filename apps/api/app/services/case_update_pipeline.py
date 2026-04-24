from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from app.services.case_chunker import build_case_chunks
from app.services.case_deduper import find_existing_case
from app.services.case_metadata_extractor import extract_case_metadata
from app.services.case_sources import get_case_sources
from app.services.case_upsert import upsert_case_with_chunks


@dataclass
class CaseUpdateReport:
    fetched: int = 0
    inserted: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)


class CaseUpdatePipeline:
    def __init__(self, db: Session):
        self.db = db

    def run(self, raw_case_items: list[dict[str, Any]]) -> CaseUpdateReport:
        report = CaseUpdateReport()
        sources = get_case_sources()

        enabled_sources = [s for s in sources if s.enabled]
        if not enabled_sources:
            report.errors.append("No enabled case sources configured.")
            return report

        for raw in raw_case_items:
            report.fetched += 1

            try:
                metadata = extract_case_metadata(raw)

                existing = find_existing_case(
                    db=self.db,
                    normalized_case_name=metadata["normalized_case_name"],
                    citation=metadata.get("citation"),
                    year=metadata.get("year"),
                )

                chunks = build_case_chunks(metadata)
                if not chunks:
                    report.skipped += 1
                    continue

                _case, action = upsert_case_with_chunks(
                    db=self.db,
                    existing_case=existing,
                    metadata=metadata,
                    chunks=chunks,
                )

                if action == "inserted":
                    report.inserted += 1
                else:
                    report.updated += 1

            except Exception as exc:
                report.failed += 1
                report.errors.append(str(exc))

        self.db.commit()
        return report