from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CaseSourceConfig:
    source_name: str
    source_type: str
    enabled: bool
    fetch_mode: str  # "manual", "api", "scrape"
    jurisdiction: str = "Nigeria"
    court_scope: str | None = None


def get_case_sources() -> list[CaseSourceConfig]:
    return [
        CaseSourceConfig(
            source_name="manual_curated_cases",
            source_type="case_law",
            enabled=True,
            fetch_mode="manual",
            jurisdiction="Nigeria",
            court_scope="all",
        ),
    ]