from app.core.database import Base, engine
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.legal_source import LegalSource
from app.models.legal_chunk import LegalChunk


def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")


if __name__ == "__main__":
    init_db()