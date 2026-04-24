from pydantic import BaseModel
from typing import Optional, List


class LegalSearchRequest(BaseModel):
    query: str
    limit: int = 5


class LegalSearchResult(BaseModel):
    source_id: int
    source_title: str
    part_label: Optional[str] = None
    section_number: Optional[str] = None
    side_note: Optional[str] = None
    text: str


class LegalSearchResponse(BaseModel):
    query: str
    count: int
    results: List[LegalSearchResult]