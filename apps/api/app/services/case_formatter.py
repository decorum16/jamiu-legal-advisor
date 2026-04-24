from typing import Any


def chunk_priority(chunk_type: str | None) -> int:
    value = (chunk_type or "").strip().lower()

    if value == "ratio":
        return 4
    if value == "holding":
        return 3
    if value == "issue":
        return 2
    if value == "facts":
        return 1
    return 0


def court_priority(court_level: str | None) -> int:
    value = (court_level or "").strip().lower()

    if value == "supreme":
        return 3
    if value == "appeal":
        return 2
    if value == "high_court":
        return 1
    return 0


def format_case_support(case_chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best_by_case: dict[str, dict[str, Any]] = {}

    for item in case_chunks:
        case_name = (item.get("case_name") or "").strip()
        if not case_name:
            continue

        existing = best_by_case.get(case_name)

        if not existing:
            best_by_case[case_name] = item
            continue

        current_chunk_priority = chunk_priority(item.get("chunk_type"))
        existing_chunk_priority = chunk_priority(existing.get("chunk_type"))

        current_court_priority = court_priority(item.get("court_level"))
        existing_court_priority = court_priority(existing.get("court_level"))

        current_year = item.get("year") or 0
        existing_year = existing.get("year") or 0

        current_score = (
            current_chunk_priority,
            current_court_priority,
            current_year,
        )
        existing_score = (
            existing_chunk_priority,
            existing_court_priority,
            existing_year,
        )

        if current_score > existing_score:
            best_by_case[case_name] = item

    output = [
        {
            "case_name": item.get("case_name", ""),
            "citation": item.get("citation"),
            "court": item.get("court", ""),
            "court_level": item.get("court_level", ""),
            "year": item.get("year"),
            "chunk_type": item.get("chunk_type", ""),
            "heading": item.get("heading"),
        }
        for item in best_by_case.values()
    ]

    output.sort(
        key=lambda x: (
            court_priority(x.get("court_level")),
            x.get("year") or 0,
            chunk_priority(x.get("chunk_type")),
        ),
        reverse=True,
    )

    return output