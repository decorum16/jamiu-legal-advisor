from __future__ import annotations

import re
from typing import Any


def normalize_case_name(case_name: str) -> str:
    value = (case_name or "").strip().lower()
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def infer_court_level(court: str | None) -> str:
    value = (court or "").lower()

    if "supreme" in value:
        return "supreme"
    if "appeal" in value:
        return "appeal"
    if "high court" in value or "federal high" in value:
        return "high_court"
    return "other"


def extract_year(text: str) -> int | None:
    matches = re.findall(r"\b(19\d{2}|20\d{2})\b", text or "")
    if not matches:
        return None
    try:
        return int(matches[0])
    except Exception:
        return None


def extract_case_metadata(raw: dict[str, Any]) -> dict[str, Any]:
    case_name = raw.get("case_name") or raw.get("title") or "Unknown Case"
    citation = raw.get("citation")
    court = raw.get("court")
    summary = raw.get("summary") or ""
    subject_area = raw.get("subject_area") or "general"
    body_text = raw.get("text") or ""

    year = raw.get("year")
    if year is None:
        year = extract_year(f"{citation or ''} {body_text}")

    court_level = raw.get("court_level")
    if not court_level:
        court_level = infer_court_level(court)

    return {
        "case_name": case_name,
        "normalized_case_name": normalize_case_name(case_name),
        "citation": citation,
        "court": court,
        "court_level": court_level,
        "year": year,
        "subject_area": subject_area,
        "summary": summary,
        "text": body_text,
    }