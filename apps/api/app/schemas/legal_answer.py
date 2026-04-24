from pydantic import BaseModel
from typing import List, Optional


class LegalAnswerRequest(BaseModel):
    question: str
    limit: int = 5


class LegalAnswerCitation(BaseModel):
    source_title: str
    part_label: Optional[str] = None
    section_number: Optional[str] = None
    side_note: Optional[str] = None


class LegalAnswerResponse(BaseModel):
    question: str
    source_summary: str
    plain_explanation: str
    legal_text: str
    citations: List[LegalAnswerCitation]
    supporting_citations: List[LegalAnswerCitation]