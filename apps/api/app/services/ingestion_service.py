import re
from dataclasses import dataclass

from openai import OpenAI
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.legal_document import LegalDocument
from app.models.legal_chunk import LegalChunk

settings = get_settings()
client = OpenAI(api_key=settings.openai_api_key)


@dataclass
class ParsedSection:
    section_label: str
    citation: str
    text: str
    topic: str | None = None


class LegalIngestionService:
    def __init__(self, db: Session):
        self.db = db

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        response = client.embeddings.create(
            model=settings.embedding_model,
            input=texts,
        )
        return [item.embedding for item in response.data]

    def split_statute_sections(self, raw_text: str, short_code: str) -> list[ParsedSection]:
        raw_text = raw_text.replace("\r", "\n")

        pattern = r"(SECTION\s+\d+|Section\s+\d+|\n\d{1,3}\.\s)"
        matches = list(re.finditer(pattern, raw_text))

        sections: list[ParsedSection] = []

        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(raw_text)

            section_text = raw_text[start:end].strip()

            label_match = re.search(r"(SECTION\s+\d+|Section\s+\d+|\d{1,3})", section_text)
            if not label_match:
                continue

            label_raw = label_match.group(1)

            number_match = re.search(r"\d+", label_raw)
            if not number_match:
                continue

            section_label = f"Section {number_match.group()}"

            sections.append(
                ParsedSection(
                    section_label=section_label,
                    citation=f"{short_code}, {section_label}",
                    text=section_text,
                )
            )

        return sections

    def ingest_document(
        self,
        *,
        title: str,
        short_code: str,
        source_type: str,
        raw_text: str,
        jurisdiction: str = "Nigeria",
        version_label: str | None = None,
        source_url: str | None = None,
    ) -> LegalDocument:
        existing = self.db.scalar(
            select(LegalDocument).where(LegalDocument.short_code == short_code)
        )

        if existing:
            self.db.query(LegalChunk).filter(
                LegalChunk.document_id == existing.id
            ).delete()

            document = existing
            document.title = title
            document.source_type = source_type
            document.jurisdiction = jurisdiction
            document.version_label = version_label
            document.source_url = source_url
        else:
            document = LegalDocument(
                title=title,
                short_code=short_code,
                source_type=source_type,
                jurisdiction=jurisdiction,
                version_label=version_label,
                source_url=source_url,
            )
            self.db.add(document)
            self.db.flush()

        sections = self.split_statute_sections(raw_text, short_code)
        print(f"Parsed sections: {len(sections)}")

        if not sections:
            raise ValueError("No sections were parsed from the source text.")

        embeddings = self.embed_texts([section.text for section in sections])

        for idx, (section, embedding) in enumerate(zip(sections, embeddings)):
            chunk = LegalChunk(
                document_id=document.id,
                chunk_index=idx,
                section_label=section.section_label,
                citation=section.citation,
                topic=section.topic,
                text=section.text,
                embedding=embedding,
            )
            self.db.add(chunk)

        self.db.commit()
        self.db.refresh(document)
        return document