from __future__ import annotations

from typing import Any

from app.services.legal.answer_context import build_authority_context
from app.services.legal.authority_router import get_authority_priority
from app.services.legal.legal_intent import classify_legal_intent
from app.services.legal.normalizers import (
    normalize_case_result,
    normalize_constitution_result,
    normalize_statute_result,
)
from app.services.legal.prompts import ANSWER_SYSTEM_PROMPT, build_answer_user_prompt
from app.services.legal.ranker import rerank_authorities
from app.services.legal.selection import (
    select_lead_authority,
    select_supporting_authorities,
)
from app.services.legal.types import RetrievedAuthority


class LegalAnswerPipeline:
    def __init__(
        self,
        statute_retriever,
        constitution_retriever,
        case_retriever,
        llm_client,
    ) -> None:
        self.statute_retriever = statute_retriever
        self.constitution_retriever = constitution_retriever
        self.case_retriever = case_retriever
        self.llm_client = llm_client

    def answer(self, question: str, limit: int = 5) -> dict[str, Any]:
        intent = classify_legal_intent(question)
        priority = get_authority_priority(intent)

        raw_statutes = self._safe_retrieve(self.statute_retriever, question, limit=limit)
        raw_constitution = self._safe_retrieve(self.constitution_retriever, question, limit=limit)
        raw_cases = self._safe_retrieve(self.case_retriever, question, limit=limit)

        normalized: list[RetrievedAuthority] = []
        normalized.extend(normalize_statute_result(x) for x in raw_statutes)
        normalized.extend(normalize_constitution_result(x) for x in raw_constitution)
        normalized.extend(normalize_case_result(x) for x in raw_cases)

        ranked = rerank_authorities(question, normalized, priority)
        lead = select_lead_authority(ranked, priority)
        supporting = select_supporting_authorities(
            query=question,
            ranked_items=ranked,
            lead=lead,
            max_items=3,
        )

        authority_context = build_authority_context(lead, supporting)

        llm_output = self.llm_client.generate_json(
            system_prompt=ANSWER_SYSTEM_PROMPT,
            user_prompt=build_answer_user_prompt(question, authority_context),
        )

        return {
            "question": question,
            "intent": intent,
            "authority_priority": priority,
            "issue": llm_output.get("issue"),
            "short_answer": llm_output.get("short_answer"),
            "leading_authority": llm_output.get("leading_authority"),
            "rule_explanation": llm_output.get("rule_explanation"),
            "application": llm_output.get("application"),
            "conclusion": llm_output.get("conclusion"),
            "supporting_authorities": llm_output.get("supporting_authorities", []),
            "retrieval_debug": {
                "lead": self._to_debug_dict(lead),
                "supporting": [self._to_debug_dict(x) for x in supporting],
                "top_ranked": [self._to_debug_dict(x) for x in ranked[:5]],
            },
        }

    def _safe_retrieve(self, retriever, question: str, limit: int = 5) -> list[dict]:
        try:
            result = retriever.search(question=question, limit=limit)
            return result or []
        except Exception:
            return []

    def _to_debug_dict(self, item: RetrievedAuthority | None) -> dict[str, Any] | None:
        if not item:
            return None

        return {
            "source_type": item.source_type,
            "source_name": item.source_name,
            "citation": item.citation,
            "court": item.court,
            "year": item.year,
            "semantic_score": item.semantic_score,
            "keyword_score": item.keyword_score,
            "authority_score": item.authority_score,
            "source_quality_score": item.source_quality_score,
            "final_score": item.final_score,
        }