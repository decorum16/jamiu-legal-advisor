from __future__ import annotations

from typing import Any


def split_paragraphs(text: str) -> list[str]:
    parts = [p.strip() for p in (text or "").split("\n\n")]
    return [p for p in parts if p]


def classify_chunk_type(text: str) -> str:
    value = (text or "").lower()

    if any(word in value for word in ["held that", "the court held", "ratio", "we hold"]):
        return "ratio"

    if any(word in value for word in ["issue for determination", "issue is whether"]):
        return "issue"

    if any(word in value for word in ["facts", "the facts are", "brief facts"]):
        return "facts"

    if any(word in value for word in ["it is ordered", "conviction upheld", "appeal dismissed", "appeal allowed"]):
        return "holding"

    return "holding"


def build_case_chunks(case_metadata: dict[str, Any]) -> list[dict[str, Any]]:
    text = case_metadata.get("text") or ""
    paragraphs = split_paragraphs(text)

    chunks: list[dict[str, Any]] = []

    if not paragraphs:
        return chunks

    for idx, paragraph in enumerate(paragraphs, start=1):
        chunks.append(
            {
                "chunk_order": idx,
                "chunk_type": classify_chunk_type(paragraph),
                "heading": None,
                "text": paragraph,
            }
        )

    return chunks