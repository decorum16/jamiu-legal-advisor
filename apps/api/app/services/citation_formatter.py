from typing import Any


def format_citations(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    output: list[dict[str, Any]] = []

    for chunk in chunks:
        key = (
            (chunk.get("source_title") or "").strip().lower(),
            str(chunk.get("section_number") or "").strip().lower(),
        )
        if key in seen:
            continue
        seen.add(key)

        output.append(
            {
                "source_title": chunk.get("source_title", ""),
                "part_label": chunk.get("part_label"),
                "section_number": str(chunk.get("section_number", "")),
                "side_note": chunk.get("side_note"),
            }
        )

    return output