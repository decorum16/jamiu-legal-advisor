from __future__ import annotations


def get_authority_priority(intent: str) -> list[str]:
    """
    Returns source preference order.
    """
    if intent == "constitutional":
        return ["constitution", "statute", "case"]

    if intent == "statutory":
        return ["statute", "constitution", "case"]

    if intent == "case_law":
        return ["case", "statute", "constitution"]

    return ["statute", "constitution", "case"]