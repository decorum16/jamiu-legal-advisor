from pydantic import BaseModel
from typing import Optional


class CitationOut(BaseModel):
    source_title: str
    part_label: Optional[str] = None
    section_number: str
    side_note: Optional[str] = None


class CaseCitationOut(BaseModel):
    case_name: str
    citation: Optional[str] = None
    court: str
    court_level: str
    year: Optional[int] = None
    chunk_type: str
    heading: Optional[str] = None


class AnswerResponse(BaseModel):
    question: str
    issue: str
    short_answer: str
    rule_explanation: str
    plain_explanation: str
    practical_note: str
    limits: str
    citations: list[CitationOut]
    supporting_citations: list[CitationOut]
    case_support: list[CaseCitationOut] = []