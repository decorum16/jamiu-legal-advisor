from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.conversation import Conversation
from app.models.user import User
from app.schemas.chat import AskRequest, AskResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/ask", tags=["ask"])


@router.post("", response_model=AskResponse)
def ask(
    payload: AskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation = db.scalar(
        select(Conversation).where(
            Conversation.id == payload.conversation_id,
            Conversation.user_id == current_user.id,
        )
    )

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    chat_service = ChatService(db)
    assistant_message = chat_service.ask(
        conversation=conversation,
        user_message=payload.message,
    )

    return AskResponse(
        conversation_id=conversation.id,
        answer=assistant_message.content,
    )