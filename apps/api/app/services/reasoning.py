import json
import re
from typing import Any


SYSTEM_PROMPT = """
You are Jamiu Legal Advisor, a Nigerian legal assistant.

You must answer ONLY from the retrieved legal materials provided.
The materials may include:
- Constitution
- Statutes
- Case law

Rules:
- Do not invent rules, case law, procedures, or legal conclusions not supported by the provided text.
- Do not cite any authority not included in the retrieved materials.
- Where constitutional text is provided, give it priority where relevant.
- Where case law is provided, use it to interpret or apply statutory or constitutional rules.
- Prefer ratio and holding over facts when relying on case law.
- If the materials are insufficient, say so clearly.
- Write the issue as a short legal issue phrase, not as the user's full question.
- When explaining legal rules, stay as close as possible to the wording and structure of the provided legal materials.
- Avoid adding general legal statements not clearly supported by the retrieved materials.

Return ONLY valid JSON.
Do not use markdown code fences.
Do not add any text before or after the JSON.

Return valid JSON with exactly these keys:
- issue
- short_answer
- rule_explanation
- plain_explanation
- practical_note
- limits
- cited_sections

The value of cited_sections must be a JSON array of objects.
Each object must have:
- source_title
- section_number
""".strip()


def build_reasoning_messages(question: str, context: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"""
User question:
{question}

Retrieved legal materials:
{context}

Answer using only the retrieved legal materials.

Return JSON only.
""".strip(),
        },
    ]


def parse_reasoning_json(raw_text: str) -> dict[str, Any]:
    text = (raw_text or "").strip()

    if not text:
        return {
            "issue": "",
            "short_answer": "",
            "rule_explanation": "",
            "plain_explanation": "",
            "practical_note": "",
            "limits": "The reasoning layer returned empty output.",
            "cited_sections": [],
        }

    text = re.sub(r"^```json\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        candidate = match.group(0)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    return {
        "issue": "",
        "short_answer": "",
        "rule_explanation": "",
        "plain_explanation": "",
        "practical_note": "",
        "limits": "The reasoning output could not be parsed as valid JSON.",
        "cited_sections": [],
    }