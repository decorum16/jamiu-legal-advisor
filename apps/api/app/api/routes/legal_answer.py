from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.dependencies.db import get_db
from app.services.legal_answer import LegalAnswerService

router = APIRouter(prefix="/answer", tags=["Legal Answer"])


class LegalAnswerRequest(BaseModel):
    question: str
    limit: int = 5


@router.post("")
def legal_answer(
    payload: LegalAnswerRequest,
    db: Session = Depends(get_db),
):
    service = LegalAnswerService(db)
    return service.answer(
        question=payload.question,
        limit=payload.limit,
    )