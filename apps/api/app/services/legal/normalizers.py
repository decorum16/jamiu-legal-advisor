from __future__ import annotations

from app.services.legal.types import RetrievedAuthority


def normalize_statute_result(item: dict[str, Any]) -> RetrievedAuthority:
    citation = item.get("citation") or item.get("source_title") or "Statute"
    text = item.get("text") or ""

    keyword_score = int((item.get("score") or 0) * 100)

    authority_score = 75
    title = (item.get("source_title") or "").lower()
    if "evidence act" in title:
        authority_score = 88
    elif "administration of criminal justice" in title or "acja" in title:
        authority_score = 86
    elif "police act" in title:
        authority_score = 84

    return RetrievedAuthority(
        source_type="statute",
        source_name=item.get("source_title") or "Statute",
        citation=citation,
        text=text,
        semantic_score=0,
        keyword_score=keyword_score,
        authority_score=authority_score,
        source_quality_score=80,
        final_score=0,
        section_number=item.get("section_number"),
        part_label=item.get("part_label"),
        side_note=item.get("side_note"),
        court=None,
        year=None,
        case_name=None,
    )


def normalize_constitution_result(item: dict[str, Any]) -> RetrievedAuthority:
    citation = item.get("citation") or item.get("source_title") or "Constitution"
    text = item.get("text") or ""

    keyword_score = int((item.get("score") or 0) * 100)

    return RetrievedAuthority(
        source_type="constitution",
        source_name=item.get("source_title") or "Constitution of the Federal Republic of Nigeria 1999",
        citation=citation,
        text=text,
        semantic_score=0,
        keyword_score=keyword_score,
        authority_score=95,
        source_quality_score=95,
        final_score=0,
        section_number=item.get("section_number"),
        part_label=item.get("part_label"),
        side_note=item.get("side_note"),
        court=None,
        year=None,
        case_name=None,
    )


def normalize_case_result(item: dict) -> RetrievedAuthority:
    return RetrievedAuthority(
        source_type="case",
        source_name=item.get("case_name"),
        citation=item.get("citation"),
        text=item.get("text"),
        court=item.get("court"),
        year=item.get("year"),
        case_name=item.get("case_name"),
        semantic_score=0,
        keyword_score=0,
        authority_score=0,
        source_quality_score=0,
        final_score=0,
    )

    return RetrievedAuthority(
        source_type="case",
        source_name=item.get("case_name") or "Case Law",
        citation=citation,
        text=text,
        semantic_score=0,
        keyword_score=keyword_score,
        authority_score=authority_score,
        source_quality_score=88,
        final_score=0,
        section_number=None,
        part_label=None,
        side_note=item.get("heading"),
        court=court,
        year=item.get("year"),
        case_name=item.get("case_name"),
    )