from typing import Any


def build_legal_context(
    statute_chunks: list[dict[str, Any]],
    case_chunks: list[dict[str, Any]] | None = None,
) -> str:
    blocks: list[str] = []

    for idx, chunk in enumerate(statute_chunks, start=1):
        source_title = chunk.get("source_title", "")
        source_type = chunk.get("source_type", "statute")
        jurisdiction = chunk.get("jurisdiction", "federal")
        part_label = chunk.get("part_label", "")
        section_number = chunk.get("section_number", "")
        side_note = chunk.get("side_note", "")
        text = chunk.get("text", "")

        block = f"""
[Statute Source {idx}]
Source Title: {source_title}
Source Type: {source_type}
Jurisdiction: {jurisdiction}
Part: {part_label}
Section: {section_number}
Side Note: {side_note}
Text:
{text}
""".strip()

        blocks.append(block)

    if case_chunks:
        for idx, chunk in enumerate(case_chunks, start=1):
            block = f"""
[Case Source {idx}]
Case Name: {chunk.get("case_name", "")}
Citation: {chunk.get("citation", "")}
Court: {chunk.get("court", "")}
Court Level: {chunk.get("court_level", "")}
Year: {chunk.get("year", "")}
Subject Area: {chunk.get("subject_area", "")}
Chunk Type: {chunk.get("chunk_type", "")}
Heading: {chunk.get("heading", "")}
Text:
{chunk.get("text", "")}
""".strip()

            blocks.append(block)

    return "\n\n".join(blocks)