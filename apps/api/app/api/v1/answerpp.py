from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.user import User
from app.services.legal_answer import LegalAnswerService

router = APIRouter(prefix="/answer", tags=["answer"])


class AnswerRequest(BaseModel):
    question: str
    limit: int = 5


@router.post("")
def answer_question(
    payload: AnswerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = LegalAnswerService(db)
    return service.answer(question=payload.question, limit=payload.limit)