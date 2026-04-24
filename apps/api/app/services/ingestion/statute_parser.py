from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import List, Optional


PART_HEADING_RE = re.compile(r"^\s*PART\s+[IVXLC0-9A-Z\-–]+\s*[-–]?\s*.*$", re.IGNORECASE)
SECTION_START_RE = re.compile(r"^\s*(\d{1,4})\.\s*(.*)$")
SUBSECTION_START_RE = re.compile(r"^\s*\((\d+)\)\s*(.*)$")
PARAGRAPH_START_RE = re.compile(r"^\s*\(([a-z])\)\s*(.*)$")
SCHEDULE_HEADING_RE = re.compile(
    r"^\s*(FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|NINTH|TENTH)\s+SCHEDULE\b.*$",
    re.IGNORECASE,
)
FORM_HEADING_RE = re.compile(r"^\s*FORM\s+\d+[A-Z]?\b.*$", re.IGNORECASE)


@dataclass
class LegalChunk:
    source_title: str
    part_label: Optional[str]
    section_number: Optional[str]
    section_title: Optional[str]
    side_note: Optional[str]
    content_type: str
    text: str

    def to_dict(self) -> dict:
        return asdict(self)


def normalize_text(raw_text: str) -> str:
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u00a0", " ")
    text = text.replace("â€“", "-").replace("â€”", "-")
    text = text.replace("–", "-").replace("—", "-")
    text = text.replace("PÃLICE", "POLICE")
    text = text.replace("PÓLICE", "POLICE")
    text = text.replace("PÃ³LICE", "POLICE")
    text = text.replace("Niĝeria", "Nigeria")
    text = text.replace("InspectorGeneral", "Inspector-General")
    text = text.replace("InspectorGENERAL", "Inspector-General")
    text = text.replace("INSPECTORGENERAL", "INSPECTOR-GENERAL")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_line(line: str) -> str:
    return re.sub(r"\s+", " ", line).strip()


def is_part_heading(line: str) -> bool:
    return bool(PART_HEADING_RE.match(line))


def is_section_start(line: str) -> bool:
    return bool(SECTION_START_RE.match(line))


def is_subsection_start(line: str) -> bool:
    return bool(SUBSECTION_START_RE.match(line))


def is_paragraph_start(line: str) -> bool:
    return bool(PARAGRAPH_START_RE.match(line))


def is_schedule_heading(line: str) -> bool:
    return bool(SCHEDULE_HEADING_RE.match(line))


def is_form_heading(line: str) -> bool:
    return bool(FORM_HEADING_RE.match(line))


def clean_side_note(text: str | None) -> str | None:
    if not text:
        return None

    t = text.strip()
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"[;,:.\-]+$", "", t).strip()

    if not t:
        return None

    lower = t.lower()

    bad_exact = {
        "this act",
        "and",
        "or",
        "suspect",
        "force",
        "question",
        "prohibited",
        "act",
    }
    if lower in bad_exact:
        return None

    if len(t.split()) < 2:
        return None

    bad_starts = (
        "this act",
        "of the",
        "in the",
        "under the",
        "to the",
        "and the",
        "or the",
    )
    if lower.startswith(bad_starts):
        return None

    return t


def looks_like_side_note_line(line: str) -> bool:
    """
    Conservative side-note detection.
    Important: never classify obvious body/provision lines as side notes.
    """
    if not line:
        return False

    if is_part_heading(line) or is_section_start(line):
        return False

    if is_subsection_start(line) or is_paragraph_start(line):
        return False

    if is_schedule_heading(line) or is_form_heading(line):
        return False

    upper = line.upper()
    lower = line.lower()

    if "ADMINISTRATION OF CRIMINAL JUSTICE ACT" in upper:
        return False
    if "POLICE ACT" in upper:
        return False
    if "COMMENCEMENT" in upper:
        return False
    if "ENACTED" in upper:
        return False
    if "FEDERAL REPUBLIC" in upper:
        return False

    if line.startswith("{") or line.endswith("}"):
        return False

    words = line.split()

    # Short title-like phrases only
    if len(words) < 2 or len(words) > 7:
        return False

    # Body/provision lines often start like these
    bad_starts = (
        "where ",
        "provided ",
        "subject ",
        "without prejudice ",
        "there is ",
        "there shall ",
        "a suspect ",
        "a person ",
        "a police officer ",
        "the police ",
        "the force ",
        "members of ",
        "be ",
        "have ",
        "shall ",
    )
    if lower.startswith(bad_starts):
        return False

    # Provision lines often end like these
    if line.endswith(";") or line.endswith(":"):
        return False

    # Long sentence-like lines ending in period are probably body text
    if line.endswith(".") and len(words) > 5:
        return False

    return True


def extract_section_number_and_title(line: str) -> tuple[Optional[str], Optional[str]]:
    match = SECTION_START_RE.match(line)
    if not match:
        return None, None

    section_number = match.group(1)
    remainder = clean_line(match.group(2))

    # Keep section title as None for now
    return section_number, None


def parse_statute_text(
    raw_text: str,
    source_title: str = "Statute",
) -> List[LegalChunk]:
    text = normalize_text(raw_text)
    raw_lines = text.split("\n")
    lines = [clean_line(line) for line in raw_lines]
    lines = [line for line in lines if line]

    chunks: List[LegalChunk] = []

    current_part: Optional[str] = None
    current_section_number: Optional[str] = None
    current_section_title: Optional[str] = None
    current_section_lines: List[str] = []
    current_side_note: Optional[str] = None
    current_mode: str = "main_section"

    def flush_section() -> None:
        nonlocal current_section_number
        nonlocal current_section_title
        nonlocal current_section_lines
        nonlocal current_side_note
        nonlocal current_mode

        if current_section_number is None and not current_section_lines:
            return

        body = "\n".join(current_section_lines).strip()
        if body:
            chunks.append(
                LegalChunk(
                    source_title=source_title,
                    part_label=current_part,
                    section_number=current_section_number,
                    section_title=current_section_title,
                    side_note=clean_side_note(current_side_note),
                    content_type=current_mode,
                    text=body,
                )
            )

        current_section_number = None
        current_section_title = None
        current_section_lines = []
        current_side_note = None
        current_mode = "main_section"

    i = 0
    while i < len(lines):
        line = lines[i]

        if is_part_heading(line):
            # Special case:
            # if we just opened a section like "3." and the next content is a Part heading,
            # do NOT flush the section yet. Some extracted statutes place the Part heading
            # between the section number and the body text.
            if (
                current_section_number is not None
                and len(current_section_lines) == 1
                and current_section_lines[0].strip() == f"{current_section_number}."
            ):
                current_part = line
                i += 1
                continue

            flush_section()
            current_part = line
            i += 1
            continue

        if is_schedule_heading(line):
            flush_section()
            chunks.append(
                LegalChunk(
                    source_title=source_title,
                    part_label=current_part,
                    section_number=None,
                    section_title=line,
                    side_note=None,
                    content_type="schedule_heading",
                    text=line,
                )
            )
            i += 1
            continue

        if is_form_heading(line):
            flush_section()
            chunks.append(
                LegalChunk(
                    source_title=source_title,
                    part_label=current_part,
                    section_number=None,
                    section_title=line,
                    side_note=None,
                    content_type="form_heading",
                    text=line,
                )
            )
            i += 1
            continue

        if is_section_start(line):
            flush_section()
            section_number, section_title = extract_section_number_and_title(line)
            current_section_number = section_number
            current_section_title = section_title
            current_section_lines = [line]
            current_mode = "main_section"
            i += 1
            continue

        if current_section_number is not None:
            # Only attach as side note if:
            # 1. current body is still very short
            # 2. line really looks like a short marginal label
            if (
                len(current_section_lines) <= 1
                and current_side_note is None
                and looks_like_side_note_line(line)
            ):
                cleaned = clean_side_note(line)
                if cleaned:
                    current_side_note = cleaned
                    i += 1
                    continue

            # Otherwise, treat it as body text
            current_section_lines.append(line)
            i += 1
            continue

        # Anything outside a section becomes front matter
        chunks.append(
            LegalChunk(
                source_title=source_title,
                part_label=current_part,
                section_number=None,
                section_title=None,
                side_note=None,
                content_type="front_matter",
                text=line,
            )
        )
        i += 1

    flush_section()
    return chunks