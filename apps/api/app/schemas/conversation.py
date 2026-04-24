from datetime import datetime
from pydantic import BaseModel

from app.models.user import UserRole


class ConversationCreate(BaseModel):
    title: str | None = None
    mode: UserRole


class ConversationOut(BaseModel):
    id: int
    user_id: int
    title: str | None
    mode: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}