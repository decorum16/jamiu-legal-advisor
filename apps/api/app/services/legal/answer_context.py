from __future__ import annotations

from app.services.legal.types import RetrievedAuthority


def build_authority_context(
    lead: RetrievedAuthority | None,
    supporting: list[RetrievedAuthority],
) -> str:
    lines: list[str] = []

    if lead:
        lines.append("LEAD AUTHORITY")
        lines.append(f"Type: {lead.source_type}")
        lines.append(f"Name: {lead.source_name}")
        lines.append(f"Citation: {lead.citation}")
        if lead.court:
            lines.append(f"Court: {lead.court}")
        if lead.year:
            lines.append(f"Year: {lead.year}")
        lines.append("Text:")
        lines.append(lead.text.strip())
        lines.append("")

    if supporting:
        lines.append("SUPPORTING AUTHORITIES")
        for idx, item in enumerate(supporting, start=1):
            lines.append(f"{idx}. Type: {item.source_type}")
            lines.append(f"   Name: {item.source_name}")
            lines.append(f"   Citation: {item.citation}")
            if item.court:
                lines.append(f"   Court: {item.court}")
            if item.year:
                lines.append(f"   Year: {item.year}")
            lines.append(f"   Text: {item.text.strip()}")
            lines.append("")

    return "\n".join(lines)