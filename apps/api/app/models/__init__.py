from app.models.user import User, UserRole
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.legal_document import LegalDocument
from app.models.legal_chunk import LegalChunk

# ✅ ADD THIS
from app.models.case_law import LegalCase, LegalCaseChunk


__all__ = [
    "User",
    "UserRole",
    "Conversation",
    "Message",
    "LegalDocument",
    "LegalChunk",
    "LegalCase",
    "LegalCaseChunk",
]