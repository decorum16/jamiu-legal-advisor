from __future__ import annotations

from app.services.legal.types import RetrievedAuthority


def _priority_bonus(source_type: str, priority_order: list[str]) -> int:
    try:
        index = priority_order.index(source_type)
    except ValueError:
        return 0

    if index == 0:
        return 35
    if index == 1:
        return 20
    if index == 2:
        return 10
    return 0


def _source_quality_bonus(item: RetrievedAuthority) -> int:
    bonus = 0

    if item.source_type == "constitution":
        bonus += 90
    elif item.source_type == "statute":
        bonus += 80
    elif item.source_type == "case":
        bonus += 85

    if item.source_type == "case":
        court_level = (item.court or "").lower()
        if "supreme" in court_level:
            bonus += 35
        elif "appeal" in court_level:
            bonus += 25
        elif "high" in court_level:
            bonus += 15

        if item.year:
            if item.year >= 2000:
                bonus += 8
            elif item.year >= 1980:
                bonus += 5

    return bonus


def _content_bonus(query: str, item: RetrievedAuthority) -> int:
    q = query.lower()
    text = (item.text or "").lower()
    citation = (item.citation or "").lower()
    source_name = (item.source_name or "").lower()
    case_name = (item.case_name or "").lower()

    bonus = 0

    if "confession" in q:
        if "confession" in text or "confession" in citation or "confession" in source_name:
            bonus += 20

    if "conviction" in q:
        if "conviction" in text:
            bonus += 15

    if "detention" in q or "detain" in q or "liberty" in q:
        if "section 35" in citation or "personal liberty" in text:
            bonus += 30
        if "detention" in text or "detained" in text:
            bonus += 12

    if "bail" in q:
        if "bail" in text or "bail" in citation:
            bonus += 18

    if item.source_type == "case":
        if "ratio" in text:
            bonus += 8
        if case_name:
            bonus += 4

    return bonus


def rerank_authorities(
    query: str,
    items: list[RetrievedAuthority],
    priority_order: list[str],
) -> list[RetrievedAuthority]:
    rescored: list[RetrievedAuthority] = []

    for item in items:
        priority_bonus = _priority_bonus(item.source_type, priority_order)
        quality_bonus = _source_quality_bonus(item)
        content_bonus = _content_bonus(query, item)

        semantic_score = item.semantic_score or 0
        keyword_score = item.keyword_score or 0
        authority_score = item.authority_score or 0
        source_quality_score = item.source_quality_score or 0

        final_score = (
            semantic_score
            + keyword_score
            + authority_score
            + source_quality_score
            + priority_bonus
            + quality_bonus
            + content_bonus
        )

        item.final_score = final_score
        rescored.append(item)

    return sorted(rescored, key=lambda x: x.final_score or 0, reverse=True)