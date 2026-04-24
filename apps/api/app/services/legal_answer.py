from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.services.ai_service import generate_ai_reply
from app.services.case_retrieval import retrieve_case_chunks
from app.services.constitution_retrieval import retrieve_constitution_chunks
from app.services.statute_retrieval import retrieve_statute_chunks
from app.services.legal.answer_context import build_authority_context
from app.services.legal.authority_router import get_authority_priority
from app.services.legal.legal_intent import classify_legal_intent
from app.services.legal.normalizers import (
    normalize_case_result,
    normalize_constitution_result,
    normalize_statute_result,
)
from app.services.legal.ranker import rerank_authorities
from app.services.legal.selection import (
    select_lead_authority,
    select_supporting_authorities,
)
from app.services.legal.types import RetrievedAuthority


class LegalAnswerService:
    def __init__(self, db: Session):
        self.db = db

    def answer(self, question: str, limit: int = 5) -> dict[str, Any]:
        question = (question or "").strip()
        if not question:
            return {
                "question": "",
                "intent": "unknown",
                "authority_priority": [],
                "issue": "",
                "short_answer": "Please provide a legal question.",
                "leading_authority": "",
                "rule_explanation": "",
                "application": "",
                "conclusion": "",
                "supporting_authorities": [],
            }

        intent = classify_legal_intent(question)
        priority = get_authority_priority(intent)
        retrieval_limits = self._get_retrieval_limits(intent, limit)

        raw_statutes = retrieve_statute_chunks(
            question=question,
            db=self.db,
            limit=retrieval_limits["statute"],
        )
        raw_constitution = retrieve_constitution_chunks(
            question=question,
            db=self.db,
            limit=retrieval_limits["constitution"],
        )
        raw_cases = retrieve_case_chunks(
            question=question,
            db=self.db,
            limit=retrieval_limits["case"],
        )

        normalized: list[RetrievedAuthority] = []
        normalized.extend(normalize_statute_result(x) for x in raw_statutes)
        normalized.extend(normalize_constitution_result(x) for x in raw_constitution)
        normalized.extend(normalize_case_result(x) for x in raw_cases)

        ranked = rerank_authorities(
            query=question,
            items=normalized,
            priority_order=priority,
        )

        lead = select_lead_authority(ranked, priority)
        supporting = select_supporting_authorities(
            query=question,
            ranked_items=ranked,
            lead=lead,
            max_items=3,
        )

        confidence_band = self._assign_confidence_band(lead, supporting)
        if lead:
            lead.confidence_band = confidence_band

        authority_context = build_authority_context(lead, supporting)

        llm_output = self._generate_grounded_answer(
            question=question,
            authority_context=authority_context,
            lead=lead,
            supporting=supporting,
        )

        return {
            "question": question,
            "intent": intent,
            "authority_priority": priority,
            "issue": llm_output.get("issue", ""),
            "short_answer": llm_output.get("short_answer", ""),
            "leading_authority": llm_output.get("leading_authority", ""),
            "rule_explanation": llm_output.get("rule_explanation", ""),
            "application": llm_output.get("application", ""),
            "conclusion": llm_output.get("conclusion", ""),
            "supporting_authorities": llm_output.get("supporting_authorities", []),
        }

    def _get_retrieval_limits(self, intent: str, limit: int) -> dict[str, int]:
        safe_limit = max(1, int(limit))

        if intent == "constitutional":
            return {"constitution": min(safe_limit, 5), "statute": 3, "case": 2}

        if intent == "statutory":
            return {"statute": min(safe_limit, 5), "constitution": 2, "case": 3}

        if intent == "case_law":
            return {"case": min(safe_limit, 5), "statute": 3, "constitution": 2}

        return {"statute": min(safe_limit, 4), "constitution": 3, "case": 3}

    def _generate_grounded_answer(
        self,
        question: str,
        authority_context: str,
        lead: RetrievedAuthority | None,
        supporting: list[RetrievedAuthority],
    ) -> dict[str, Any]:
        if not lead:
            return {
                "issue": "No sufficiently relevant legal authority was retrieved.",
                "short_answer": "I could not find a grounded answer from the currently indexed authorities.",
                "leading_authority": "",
                "rule_explanation": "",
                "application": "",
                "conclusion": "Please refine the question or expand the legal sources indexed in the system.",
                "supporting_authorities": [],
            }

        doctrine_override = self._doctrine_override(question, lead, supporting)
        if doctrine_override:
            return doctrine_override

        if lead.confidence_band == "low":
            return self._safe_low_confidence_answer(
                question=question,
                lead=lead,
                supporting=supporting,
            )

        prompt = self._build_llm_prompt(question, authority_context)

        try:
            raw_reply = generate_ai_reply(
                query=prompt,
                mode="lawyer",
                context_chunks=[],
            )
            data = self._extract_json(raw_reply)
            if isinstance(data, dict):
                return self._ensure_answer_shape(data, lead, supporting)
        except Exception:
            pass

        return self._fallback_answer_from_authorities(
            question=question,
            lead=lead,
            supporting=supporting,
        )

    def _doctrine_override(
        self,
        question: str,
        lead: RetrievedAuthority,
        supporting: list[RetrievedAuthority],
    ) -> dict[str, Any] | None:
        q = question.lower()
        lead_label = self._format_leading_authority_label(lead)
        support_labels = [self._format_support_label(item) for item in supporting]

        def pick_case_authority() -> str:
            if lead.source_type == "case":
                return self._format_leading_authority_label(lead)

            for item in supporting:
                if item.source_type == "case":
                    return self._format_support_label(item)

            return lead_label

        confession_like = any(
            term in q
            for term in [
                "confession",
                "confessional statement",
                "admission by an accused",
                "clear admission",
                "admission alone",
            ]
        )

        conviction_like = any(
            term in q
            for term in [
                "conviction",
                "support conviction",
                "ground conviction",
                "alone support conviction",
            ]
        )

        retracted_like = any(
            term in q
            for term in [
                "retracted",
                "withdrawn",
                "withdrawn confession",
                "retracted confession",
                "acted upon by the court",
                "relied on",
                "used by the court",
                "still be used",
                "still be relied on",
            ]
        )

        if confession_like and conviction_like:
            case_synthesis = self._build_case_synthesis(lead, supporting)

            return {
                "issue": "Whether a confessional statement alone can sustain conviction under Nigerian law.",
                "short_answer": (
                    "Yes. A confession alone can ground conviction if it is voluntary, direct, "
                    "positive and unequivocal, and accepted by the court as true."
                ),
                "leading_authority": pick_case_authority(),
                "rule_explanation": (
                    "A voluntary, direct, positive and unequivocal confession can ground a conviction once the court "
                    "is satisfied of its truth. The court may test the confession against surrounding facts, but "
                    "corroboration is not a strict legal requirement. "
                    + case_synthesis
                ).strip(),
                "application": (
                    "Accordingly, where an accused person clearly admits the offence and the court is satisfied that "
                    "the statement is voluntary and true, conviction may rest on that confession alone."
                ),
                "conclusion": (
                    "A confession alone can sustain conviction if the court is satisfied that it is voluntary and true."
                ),
                "supporting_authorities": support_labels,
            }

        if confession_like and retracted_like:
            case_synthesis = self._build_case_synthesis(lead, supporting)

            return {
                "issue": "Whether a retracted or withdrawn confession may still be relied upon under Nigerian law.",
                "short_answer": (
                    "Yes. A retracted or withdrawn confession may still be relied upon if the court is "
                    "satisfied that it is voluntary and true."
                ),
                "leading_authority": pick_case_authority(),
                "rule_explanation": (
                    "A confession does not become inadmissible or worthless merely because it is later retracted or withdrawn. "
                    "The court will test its truth against surrounding circumstances. Corroboration is desirable but not a strict legal requirement. "
                    + case_synthesis
                ).strip(),
                "application": (
                    "Retraction calls for caution, but it does not automatically prevent the court from acting on the confession "
                    "if, after careful examination, the court is satisfied of its truth and voluntariness."
                ),
                "conclusion": (
                    "A retracted or withdrawn confession may still be acted upon where the court is satisfied that it is voluntary and true."
                ),
                "supporting_authorities": support_labels,
            }

        if "what is a confession" in q or ("evidence act" in q and "confession" in q):
            return {
                "issue": "Meaning of confession under the Evidence Act.",
                "short_answer": (
                    "A confession is an admission made by a person charged with a crime, "
                    "stating or suggesting the inference that he committed that crime."
                ),
                "leading_authority": lead_label,
                "rule_explanation": (
                    "Section 28 of the Evidence Act defines confession as an admission made at any time by a person "
                    "charged with a crime, stating or suggesting the inference that he committed that crime."
                ),
                "application": (
                    "The statutory definition is the starting point. Questions of admissibility and evidential weight "
                    "then arise under related provisions and case law."
                ),
                "conclusion": "The Evidence Act supplies the governing definition of confession.",
                "supporting_authorities": support_labels,
            }

        if "detain" in q or "detention" in q or "personal liberty" in q or "liberty" in q:
            return {
                "issue": "Whether the police may lawfully detain a suspect indefinitely under Nigerian law.",
                "short_answer": "No. The police cannot lawfully detain a suspect indefinitely.",
                "leading_authority": lead_label,
                "rule_explanation": (
                    "Section 35 of the Constitution guarantees personal liberty and requires that any person arrested "
                    "or detained be brought before a court within a reasonable time. Prolonged detention without judicial oversight is unconstitutional."
                ),
                "application": (
                    "Once a suspect is arrested, the police must act within the constitutional and statutory safeguards "
                    "that regulate detention, charging, release, and access to court."
                ),
                "conclusion": (
                    "Indefinite detention is unlawful and may be challenged as a violation of the constitutional right to personal liberty."
                ),
                "supporting_authorities": support_labels,
            }

        return None

    def _build_case_synthesis(
        self,
        lead: RetrievedAuthority,
        supporting: list[RetrievedAuthority],
    ) -> str:
        case_items: list[RetrievedAuthority] = []

        if lead.source_type == "case":
            case_items.append(lead)

        for item in supporting:
            if item.source_type == "case":
                case_items.append(item)

        seen: set[str] = set()
        unique_cases: list[RetrievedAuthority] = []

        for item in case_items:
            label = self._format_leading_authority_label(item)
            if label not in seen:
                seen.add(label)
                unique_cases.append(item)

        if not unique_cases:
            return ""

        labels = [self._format_leading_authority_label(item) for item in unique_cases[:3]]

        if len(labels) == 1:
            return f"The leading case authority is {labels[0]}."

        if len(labels) == 2:
            return f"The rule is supported by {labels[0]} and {labels[1]}."

        return f"The rule is supported by {labels[0]}, {labels[1]}, and {labels[2]}."

    def _build_llm_prompt(self, question: str, authority_context: str) -> str:
        return f"""
You are Jamiu Legal Advisor, a Nigerian legal assistant.

Answer strictly from the supplied Nigerian legal authorities.
Do not invent any statute, section, case holding, or citation.
Write like a careful Nigerian lawyer using plain English.

Rules:
- For detention, liberty, arrest-and-detention, or reasonable-time questions, lead with the Constitution before statutes.
- For direct definitional questions under an Act, lead with the statute.
- For doctrinal or judicial-treatment questions, lead with case law.
- Use established Nigerian doctrinal language where appropriate, including:
  "voluntary, direct, positive and unequivocal"
  "stating or suggesting the inference"
  "not a strict legal requirement"
- Do not state that corroboration is always required for confession unless the supplied authorities clearly say so.
- Do not let a statute displace a stronger case authority on a doctrinal question.
- Do not weaken the answer into vague generalities if the authorities support a firmer statement.

Return ONLY valid JSON with these keys:
- issue
- short_answer
- leading_authority
- rule_explanation
- application
- conclusion
- supporting_authorities

Question:
{question}

Authoritative materials:
{authority_context}
""".strip()

    def _extract_json(self, raw_reply: str) -> dict[str, Any] | None:
        raw_reply = (raw_reply or "").strip()
        if not raw_reply:
            return None

        try:
            return json.loads(raw_reply)
        except Exception:
            pass

        start = raw_reply.find("{")
        end = raw_reply.rfind("}")
        if start != -1 and end != -1 and end > start:
            chunk = raw_reply[start : end + 1]
            try:
                return json.loads(chunk)
            except Exception:
                return None

        return None

    def _fallback_answer_from_authorities(
        self,
        question: str,
        lead: RetrievedAuthority,
        supporting: list[RetrievedAuthority],
    ) -> dict[str, Any]:
        lead_label = self._format_leading_authority_label(lead)
        support_labels = [self._format_support_label(item) for item in supporting]

        rule_text = (lead.text or "").strip()
        if len(rule_text) > 700:
            rule_text = rule_text[:700].rstrip() + "..."

        application = self._build_application_text(question, lead)

        return {
            "issue": f"Whether Nigerian law permits or regulates the point raised in the question: {question}",
            "short_answer": self._build_short_answer(lead),
            "leading_authority": lead_label,
            "rule_explanation": rule_text,
            "application": application,
            "conclusion": self._build_conclusion(lead),
            "supporting_authorities": support_labels,
        }

    def _ensure_answer_shape(
        self,
        data: dict[str, Any],
        lead: RetrievedAuthority,
        supporting: list[RetrievedAuthority],
    ) -> dict[str, Any]:
        lead_label = self._format_leading_authority_label(lead)
        support_labels = [self._format_support_label(item) for item in supporting]

        leading_authority = data.get("leading_authority")
        if not isinstance(leading_authority, str):
            leading_authority = lead_label

        raw_supporting = data.get("supporting_authorities")
        normalized_support: list[str] = []
        seen: set[str] = set()

        if isinstance(raw_supporting, list):
            for item in raw_supporting:
                if isinstance(item, str):
                    value = item.strip()
                elif isinstance(item, dict):
                    if item.get("case_name") and item.get("citation"):
                        value = f"{item['case_name']} ({item['citation']})"
                    elif item.get("name") and item.get("citation"):
                        value = f"{item['name']} ({item['citation']})"
                    elif item.get("source_name") and item.get("section_number"):
                        value = f"{item['source_name']}, Section {item['section_number']}"
                    elif item.get("name"):
                        value = str(item["name"]).strip()
                    else:
                        value = ""
                else:
                    value = str(item).strip()

                if value and value not in seen:
                    seen.add(value)
                    normalized_support.append(value)

        if not normalized_support:
            normalized_support = support_labels

        return {
            "issue": data.get("issue")
            or "Whether the question is governed by Nigerian law and the retrieved authorities.",
            "short_answer": data.get("short_answer") or self._build_short_answer(lead),
            "leading_authority": leading_authority or lead_label,
            "rule_explanation": data.get("rule_explanation") or (lead.text or "").strip(),
            "application": data.get("application") or self._build_application_text("", lead),
            "conclusion": data.get("conclusion") or self._build_conclusion(lead),
            "supporting_authorities": normalized_support,
        }

    def _build_short_answer(self, lead: RetrievedAuthority) -> str:
        if lead.source_type == "constitution":
            return (
                "The question is primarily governed by the Constitution, subject to any applicable statute "
                "and judicial interpretation."
            )

        if lead.source_type == "statute":
            return (
                "The question is primarily governed by the relevant statutory provision, read together with "
                "any supporting case law."
            )

        if lead.source_type == "case":
            return (
                "The question is primarily answered by judicial authority, supported where relevant by statute "
                "or constitutional provisions."
            )

        return "The answer depends on the retrieved Nigerian legal authorities."

    def _build_application_text(self, question: str, lead: RetrievedAuthority) -> str:
        if lead.source_type == "constitution":
            return (
                "On the retrieved materials, the issue should first be approached as a constitutional question. "
                "Any arrest, detention, liberty, fair hearing, dignity, or similar rights issue should be tested "
                "against the constitutional guarantee before turning to procedural statutes."
            )

        if lead.source_type == "statute":
            return (
                "On the retrieved materials, the issue should first be approached by identifying the exact statutory "
                "section governing the procedure, definition, duty, or power in question, and then checking whether "
                "case law has interpreted that provision."
            )

        if lead.source_type == "case":
            return (
                "On the retrieved materials, the issue should first be approached through the way the courts have "
                "interpreted and applied the law. The leading case authority should guide the doctrinal position, "
                "with statute and constitutional provisions used in support where relevant."
            )

        return f"The question should be answered from the retrieved authorities: {question}"

    def _build_conclusion(self, lead: RetrievedAuthority) -> str:
        if lead.source_type == "constitution":
            return (
                "The safest grounded conclusion is the one supported first by the Constitution, then by any relevant "
                "statute and case law."
            )

        if lead.source_type == "statute":
            return (
                "The safest grounded conclusion is the one supported first by the relevant statutory provision, "
                "with case law used to explain or reinforce it."
            )

        if lead.source_type == "case":
            return (
                "The safest grounded conclusion is the one supported first by the leading judicial authority, "
                "especially where the question is doctrinal or interpretive."
            )

        return "The conclusion should remain tied to the strongest retrieved authority."

    def _format_leading_authority_label(self, item: RetrievedAuthority) -> str:
        if item.source_type == "case":
            if item.case_name and item.citation:
                return f"{item.case_name} {item.citation}"
            return item.case_name or item.citation or "Case Law"

        if item.section_number:
            return f"{item.source_name}, Section {item.section_number}"

        return item.citation or item.source_name

    def _format_support_label(self, item: RetrievedAuthority) -> str:
        if item.source_type == "case":
            if item.case_name and item.citation:
                return f"{item.case_name} {item.citation}"
            return item.case_name or item.citation or item.source_name

        if item.section_number:
            return f"{item.source_name}, Section {item.section_number}"

        return item.citation or item.source_name

    def _assign_confidence_band(
        self,
        lead: RetrievedAuthority | None,
        supporting: list[RetrievedAuthority],
    ) -> str:
        if not lead:
            return "low"

        lead_score = lead.final_score or 0
        support_count = len(supporting)

        if lead.source_type == "constitution" and lead_score >= 180:
            return "high"

        if lead.source_type == "case" and lead_score >= 190 and support_count >= 1:
            return "high"

        if lead.source_type == "statute" and lead_score >= 170:
            return "high"

        if lead_score >= 140:
            return "medium"

        return "low"

    def _safe_low_confidence_answer(
        self,
        question: str,
        lead: RetrievedAuthority | None,
        supporting: list[RetrievedAuthority],
    ) -> dict[str, Any]:
        if lead:
            override = self._doctrine_override(question, lead, supporting)
            if override:
                return override

        lead_label = self._format_leading_authority_label(lead) if lead else ""
        support_labels = [self._format_support_label(item) for item in supporting]

        return {
            "issue": f"Whether the current indexed authorities clearly answer the question: {question}",
            "short_answer": "The current indexed materials do not support a sufficiently confident legal answer yet.",
            "leading_authority": lead_label,
            "rule_explanation": (
                "Some potentially relevant authority was retrieved, but the current corpus or ranking does not yet "
                "make the legal position sufficiently secure for a firm answer."
            ),
            "application": (
                "The safer course is to refine the question, expand the indexed sources, or retrieve more directly relevant "
                "constitutional, statutory, or case-law materials before stating a definite rule."
            ),
            "conclusion": (
                "Jamiu should treat this as a low-confidence answer and avoid presenting it as settled law."
            ),
            "supporting_authorities": support_labels,
        }