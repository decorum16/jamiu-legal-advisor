from openai import OpenAI

from app.core.config import get_settings

settings = get_settings()
client = OpenAI(api_key=settings.openai_api_key)

print("OPENAI_MODEL =", settings.openai_model)


def generate_ai_reply(query: str, mode: str, context_chunks: list[str] | None = None) -> str:
    context_chunks = context_chunks or []
    context = "\n\n".join(context_chunks).strip()

    system_prompt = (
        "You are Jamiu Legal Advisor. "
        "You are focused strictly on Nigerian legal and policing context. "
        "Do not answer outside Nigerian legal context. "
        "If the issue is uncertain, say so clearly. "
        "Use ONLY the provided legal context when context is supplied. "
        "Cite sections where possible. "
        "Do not invent statutes or sections."
    )

    if mode == "police":
        system_prompt += (
            " The user is in police mode. Focus on Police Act 2020, ACJA, CFRN, "
            "lawful arrest, detention, bail, statements, search, and professional conduct."
        )
    elif mode == "lawyer":
        system_prompt += (
            " The user is in lawyer mode. Focus on Nigerian legal analysis, procedure, "
            "criminal justice, constitutional safeguards, and statutory interpretation."
        )
    elif mode == "nls_student":
        system_prompt += (
            " The user is a Nigerian Law School student. Explain clearly, simply, and accurately."
        )

    if context:
        user_prompt = f"""
Question:
{query}

Retrieved Nigerian legal context:
{context}

Answer using the context above. Cite sections where possible.
""".strip()
    else:
        user_prompt = query

    response = client.responses.create(
        model=settings.openai_model,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    return response.output_text.strip()