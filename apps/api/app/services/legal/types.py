from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RetrievedAuthority:
    source_type: str
    source_name: str
    citation: str
    text: str

    semantic_score: int = 0
    keyword_score: int = 0
    authority_score: int = 0
    source_quality_score: int = 0
    final_score: int = 0

    section_number: str | None = None
    part_label: str | None = None
    side_note: str | None = None

    court: str | None = None
    year: int | None = None
    case_name: str | None = None

    confidence_band: str | None = None