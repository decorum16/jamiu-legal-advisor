from __future__ import annotations

from app.services.legal.types import RetrievedAuthority


def select_lead_authority(
    ranked_items: list[RetrievedAuthority],
    priority_order: list[str],
) -> RetrievedAuthority | None:
    if not ranked_items:
        return None

    top_item = ranked_items[0]

    for preferred_type in priority_order:
        preferred_items = [x for x in ranked_items if x.source_type == preferred_type]
        if not preferred_items:
            continue

        best_preferred = preferred_items[0]

        if best_preferred.final_score >= top_item.final_score * 0.82:
            return best_preferred

    return top_item


def _is_relevant_support(query: str, lead: RetrievedAuthority | None, item: RetrievedAuthority) -> bool:
    q = query.lower()
    text = (item.text or "").lower()
    citation = (item.citation or "").lower()
    source_name = (item.source_name or "").lower()

    if lead and item.citation == lead.citation:
        return False

    if "confession" in q or "conviction" in q or "retracted" in q or "withdrawn" in q:
        if item.source_type == "constitution":
            return False
        if item.source_type == "statute":
            return (
                "evidence act" in source_name
                or "evidence act" in citation
                or "confession" in text
            )
        if item.source_type == "case":
            return True

    if "detention" in q or "detain" in q or "liberty" in q:
        if item.source_type == "constitution":
            return True
        if item.source_type == "statute":
            return "police act" in source_name or "acja" in source_name or "criminal justice" in source_name
        return False

    if "bail" in q:
        if item.source_type == "statute":
            return "acja" in source_name or "criminal justice" in source_name or "police act" in source_name
        if item.source_type == "case":
            return True
        return False

    return True


def select_supporting_authorities(
    query: str,
    ranked_items: list[RetrievedAuthority],
    lead: RetrievedAuthority | None,
    max_items: int = 3,
) -> list[RetrievedAuthority]:
    if not ranked_items:
        return []

    selected: list[RetrievedAuthority] = []
    seen_citations: set[str] = set()

    for item in ranked_items:
        if not _is_relevant_support(query, lead, item):
            continue
        if item.citation in seen_citations:
            continue

        seen_citations.add(item.citation)
        selected.append(item)

        if len(selected) >= max_items:
            break

    return selected[:max_items]