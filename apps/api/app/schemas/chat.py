from pydantic import BaseModel


class AskRequest(BaseModel):
    conversation_id: int
    message: str


class AskResponse(BaseModel):
    conversation_id: int
    answer: str