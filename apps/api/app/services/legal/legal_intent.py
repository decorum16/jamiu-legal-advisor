from __future__ import annotations


def classify_legal_intent(question: str) -> str:
    q = question.lower().strip()

    constitutional_terms = [
        "fundamental right",
        "fundamental rights",
        "liberty",
        "personal liberty",
        "human right",
        "human rights",
        "constitution",
        "constitutional",
        "unlawful detention",
        "wrongful detention",
        "detention without trial",
        "arrest and detention",
        "freedom",
        "fair hearing",
        "privacy",
        "dignity",
        "chapter iv",
        "chapter 4",
        "detain",
        "detention",
        "detained",
        "reasonable time",
        "24 hours",
        "48 hours",
    ]

    case_law_terms = [
        "can confession alone",
        "retracted confession",
        "judicial interpretation",
        "court held",
        "what did the court say",
        "authority",
        "precedent",
        "doctrine",
        "burden of proof",
        "whether the court can",
        "is it settled law",
        "ratio",
        "ratio decidendi",
        "ground conviction",
        "judicial treatment",
    ]

    statutory_terms = [
        "section",
        "under the act",
        "under acja",
        "under the police act",
        "under the evidence act",
        "procedure",
        "procedural",
        "how to charge",
        "arraignment",
        "bail procedure",
        "remand",
        "statement taking",
        "definition",
        "means under the act",
        "what is a confession under the evidence act",
    ]

    if any(term in q for term in constitutional_terms):
        return "constitutional"

    if any(term in q for term in case_law_terms):
        return "case_law"

    if any(term in q for term in statutory_terms):
        return "statutory"

    if any(word in q for word in ["right", "rights", "liberty", "detention", "detain", "detained"]):
        return "constitutional"

    if any(word in q for word in ["held", "decided", "court", "precedent", "conviction"]):
        return "case_law"

    return "statutory"