from typing import Any


def normalize_text(value: str | None) -> str:
    return (value or "").strip().lower()


def allowed_citation_pairs(chunks: list[dict[str, Any]]) -> set[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()

    for chunk in chunks:
        source = normalize_text(chunk.get("source_title"))
        section = normalize_text(str(chunk.get("section_number", "")))
        if source and section:
            pairs.add((source, section))

    return pairs


def validate_cited_sections(
    cited_sections: list[Any],
    chunks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    allowed = allowed_citation_pairs(chunks)
    valid: list[dict[str, Any]] = []

    for item in cited_sections:
        if not isinstance(item, dict):
            continue

        source = normalize_text(item.get("source_title"))
        section = normalize_text(str(item.get("section_number", "")))

        if (source, section) in allowed:
            valid.append(item)

    return valid