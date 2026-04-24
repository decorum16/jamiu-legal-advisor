from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import List, Optional


PART_HEADING_RE = re.compile(r"^\s*PART\s+\d+[A-Z]?\s*[-–]\s*.+$", re.IGNORECASE)
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
    """
    Light cleanup only.
    We do NOT aggressively flatten because legal hierarchy matters.
    """
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u00a0", " ")

    # Fix common mojibake / encoding artifacts
    text = text.replace("â€“", "-")
    text = text.replace("â€”", "-")
    text = text.replace("–", "-")
    text = text.replace("—", "-")

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


def looks_like_side_note_line(line: str) -> bool:
    """
    Detect marginal notes / side notes conservatively.

    Good examples:
    - Arrest generally
    - No unnecessary restraint
    - Functions of the committee
    - Secretariat of the Committee

    Bad examples:
    - 1. (1) The purpose of this Act...
    - (2) The court shall...
    - Where the Comptroller-General...
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

    # Filter noise
    if "ADMINISTRATION OF CRIMINAL JUSTICE ACT" in upper:
        return False
    if "COMMENCEMENT" in upper:
        return False
    if "ENACTED" in upper:
        return False
    if "FEDERAL REPUBLIC" in upper:
        return False

    # Reject bracket metadata
    if line.startswith("{") or line.endswith("}"):
        return False

    words = line.split()

    # Too short = likely noise
    if len(words) < 2:
        return False

    # Too long = likely body text
    if len(words) > 7:
        return False

    # Looks like real legal sentence
    if any(
        lower.startswith(x)
        for x in [
            "where ",
            "provided ",
            "subject ",
            "without prejudice ",
            "there is ",
            "there shall ",
            "a suspect ",
            "a person ",
            "a court ",
            "the court ",
            "the committee ",
            "the secretary ",
            "members of ",
            "criminal matters ",
        ]
    ):
        return False

    # Ends like body text
    if line.endswith(";") or line.endswith(":"):
        return False

    # Long sentence ending with full stop = probably body text
    if line.endswith(".") and len(words) > 5:
        return False

    return True


def join_broken_side_notes(lines: List[str]) -> List[str]:
    """
    Reconstruct side notes broken across multiple lines, e.g.

    Court may direct
    release of prisoner
    before completion
    of sentence.

    ->
    Court may direct release of prisoner before completion of sentence.
    """
    merged: List[str] = []
    i = 0

    while i < len(lines):
        current = clean_line(lines[i])

        if not current:
            i += 1
            continue

        if looks_like_side_note_line(current):
            buffer = [current]
            j = i + 1

            while j < len(lines):
                nxt = clean_line(lines[j])
                if not nxt:
                    break
                if looks_like_side_note_line(nxt):
                    buffer.append(nxt)
                    if nxt.endswith("."):
                        j += 1
                        break
                    j += 1
                    continue
                break

            merged_line = " ".join(buffer)
            merged.append(clean_line(merged_line))
            i = j
            continue

        merged.append(current)
        i += 1

    return merged


def extract_section_number_and_title(line: str) -> tuple[Optional[str], Optional[str]]:
    """
    For ACJA, the text after '1.' or '468.' is usually the operative body,
    not a true section title. So we only extract the section number and keep
    section_title as None.
    """
    match = SECTION_START_RE.match(line)
    if not match:
        return None, None

    section_number = match.group(1)
    return section_number, None


def parse_acja_text(
    raw_text: str,
    source_title: str = "Administration of Criminal Justice Act",
) -> List[LegalChunk]:
    text = normalize_text(raw_text)
    raw_lines = text.split("\n")
    cleaned_lines = [clean_line(line) for line in raw_lines]
    cleaned_lines = [line for line in cleaned_lines if line != ""]
    cleaned_lines = join_broken_side_notes(cleaned_lines)

    chunks: List[LegalChunk] = []

    current_part: Optional[str] = None
    pending_side_note: Optional[str] = None

    current_section_number: Optional[str] = None
    current_section_title: Optional[str] = None
    current_section_lines: List[str] = []

    current_mode: str = "main_section"

    def flush_section() -> None:
        nonlocal current_section_number
        nonlocal current_section_title
        nonlocal current_section_lines
        nonlocal pending_side_note
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
                    side_note=pending_side_note,
                    content_type=current_mode,
                    text=body,
                )
            )

        current_section_number = None
        current_section_title = None
        current_section_lines = []
        pending_side_note = None
        current_mode = "main_section"

    i = 0
    while i < len(cleaned_lines):
        line = cleaned_lines[i]

        if is_part_heading(line):
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

        # Side note before a section
        if current_section_number is None and looks_like_side_note_line(line):
            pending_side_note = line.rstrip(".")
            i += 1
            continue

        # Inside a section
        if current_section_number is not None:
            # If this looks like a side note and the next line starts a new section,
            # treat it as the side note for the NEXT section.
            if looks_like_side_note_line(line):
                if i + 1 < len(cleaned_lines) and is_section_start(cleaned_lines[i + 1]):
                    flush_section()
                    pending_side_note = line.rstrip(".")
                    i += 1
                    continue

                # Otherwise treat it as this section's inline side note
                if pending_side_note is None:
                    pending_side_note = line.rstrip(".")
                i += 1
                continue

            current_section_lines.append(line)
            i += 1
            continue

        # Orphan text outside sections
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