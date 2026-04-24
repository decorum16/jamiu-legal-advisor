from __future__ import annotations

from openai import OpenAI

from app.core.config import get_settings

settings = get_settings()
client = OpenAI(api_key=settings.openai_api_key)


EMBEDDING_MODEL = "text-embedding-3-small"


def build_embedding_input(text: str, max_chars: int = 6000) -> str:
    value = (text or "").strip()
    if not value:
        return ""
    return value[:max_chars]


def get_text_embedding(text: str) -> list[float] | None:
    cleaned = build_embedding_input(text)
    if not cleaned:
        return None

    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=cleaned,
    )
    return response.data[0].embedding