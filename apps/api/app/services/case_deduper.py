from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.case_law import LegalCase


def find_existing_case(
    db: Session,
    normalized_case_name: str,
    citation: str | None,
    year: int | None,
) -> LegalCase | None:
    if citation:
        existing = db.scalar(
            select(LegalCase).where(LegalCase.citation == citation)
        )
        if existing:
            return existing

    existing = db.scalar(
        select(LegalCase).where(LegalCase.case_name.ilike(normalized_case_name))
    )
    if existing:
        return existing

    if year is not None:
        existing = db.scalar(
            select(LegalCase).where(
                LegalCase.case_name.ilike(normalized_case_name),
                LegalCase.year == year,
            )
        )
        if existing:
            return existing

    return None