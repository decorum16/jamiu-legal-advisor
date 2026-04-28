from pydantic import BaseModel, Field


class LegalSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(default=5, ge=1, le=20)


class LegalSearchResult(BaseModel):
    source_title: str
    part_label: str | None = None
    section_number: str = ""
    side_note: str | None = None
    text: str


class LegalSearchResponse(BaseModel):
    query: str
    count: int
    results: list[LegalSearchResult]