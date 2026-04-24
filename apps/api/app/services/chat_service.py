from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.message import Message
from app.services.legal_answer import LegalAnswerService


class ChatService:
    def __init__(self, db: Session):
        self.db = db
        self.legal_answer_service = LegalAnswerService(db)

    def ask(
        self,
        conversation: Conversation,
        user_message: str,
    ) -> Message:
        user_message = (user_message or "").strip()

        user_msg = Message(
            conversation_id=conversation.id,
            role="user",
            content=user_message,
        )
        self.db.add(user_msg)
        self.db.flush()

        legal_result = self.legal_answer_service.answer(
            question=user_message,
            limit=5,
        )

        assistant_text = self._format_legal_result_as_chat(legal_result)

        assistant_msg = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=assistant_text,
        )
        self.db.add(assistant_msg)
        self.db.commit()
        self.db.refresh(assistant_msg)

        return assistant_msg

    def _format_legal_result_as_chat(self, result: dict) -> str:
        parts: list[str] = []

        short_answer = (result.get("short_answer") or "").strip()
        issue = (result.get("issue") or "").strip()
        leading_authority = (result.get("leading_authority") or "").strip()
        rule_explanation = (result.get("rule_explanation") or "").strip()
        application = (result.get("application") or "").strip()
        conclusion = (result.get("conclusion") or "").strip()
        supporting_authorities = result.get("supporting_authorities") or []

        if short_answer:
            parts.append(short_answer)

        if issue:
            parts.append(f"Issue: {issue}")

        if leading_authority:
            parts.append(f"Leading authority: {leading_authority}")

        if rule_explanation:
            parts.append(f"Rule: {rule_explanation}")

        if application:
            parts.append(f"Application: {application}")

        if conclusion:
            parts.append(f"Conclusion: {conclusion}")

        if supporting_authorities:
            support_lines = "\n".join(f"- {item}" for item in supporting_authorities)
            parts.append(f"Supporting authorities:\n{support_lines}")

        text = "\n\n".join(parts).strip()

        if not text:
            return "I could not produce a grounded legal answer from the currently indexed materials."

        return text