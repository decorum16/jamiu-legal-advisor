from __future__ import annotations

import re


SECTION_ONLY_RE = re.compile(r"^\d{1,4}\.$")
PART_HEADING_RE = re.compile(r"^\s*PART\s+[IVXLC0-9A-Z\-–]+\s*[-–]?\s*.*$", re.IGNORECASE)


def clean_line(line: str) -> str:
    return re.sub(r"\s+", " ", line).strip()


def is_section_only_line(line: str) -> bool:
    return bool(SECTION_ONLY_RE.match(line.strip()))


def extract_section_number(line: str) -> int | None:
    m = re.match(r"^(\d{1,4})\.", line.strip())
    if not m:
        return None
    return int(m.group(1))


def looks_like_margin_note(line: str) -> bool:
    """
    Very conservative detector for broken side-note / marginal-note lines.
    """
    if not line:
        return False

    lower = line.lower()
    words = line.split()

    if len(words) < 2 or len(words) > 8:
        return False

    if PART_HEADING_RE.match(line):
        return False

    if re.match(r"^\(\d+\)", line) or re.match(r"^\([a-z]\)", line):
        return False

    if re.match(r"^\d{1,4}\.", line):
        return False

    bad_starts = (
        "where ",
        "provided ",
        "subject ",
        "there is ",
        "there shall ",
        "a suspect ",
        "a police officer ",
        "the police ",
        "the force ",
        "shall ",
        "be ",
        "have ",
    )
    if lower.startswith(bad_starts):
        return False

    if line.endswith(";") or line.endswith(":"):
        return False

    return True


def preprocess_police_act_text(raw_text: str) -> str:
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")

    # common mojibake / extraction fixes
    replacements = {
        "â€“": "-",
        "â€”": "-",
        "–": "-",
        "—": "-",
        "PÃLICE": "POLICE",
        "PÓLICE": "POLICE",
        "PÃ³LICE": "POLICE",
        "AСT": "ACT",
        "АСТ": "ACT",
        "Niĝeria": "Nigeria",
        "ofthe": "of the",
        "shal!": "shall",
        "Commarids": "Commands",
        "Divisíonal": "Divisional",
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)

    raw_lines = [clean_line(line) for line in text.split("\n")]
    lines = [line for line in raw_lines if line]

    cleaned: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # remove repeated document-title noise
        if line.upper() in {
            "NIGERIA POLICE ACT, 2020",
            "NIGERIA POLICE ACT, 2020.",
            "NIGERIA POLICE ACT, 2020 A BILL",
            "EXPLANATORY MEMORANDUM",
        }:
            cleaned.append(line)
            i += 1
            continue

        # remove orphan standalone section numbers when immediately followed by a lower section number
        # example from your text: 4. then 3.
        if is_section_only_line(line) and i + 1 < len(lines) and is_section_only_line(lines[i + 1]):
            current_num = extract_section_number(line)
            next_num = extract_section_number(lines[i + 1])

            if current_num is not None and next_num is not None and next_num < current_num:
                i += 1
                continue

        # join standalone section number with next line if next line is body text
        if is_section_only_line(line) and i + 1 < len(lines):
            nxt = lines[i + 1]

            if (
                not is_section_only_line(nxt)
                and not PART_HEADING_RE.match(nxt)
                and not looks_like_margin_note(nxt)
            ):
                cleaned.append(f"{line} {nxt}")
                i += 2
                continue

        # drop obvious isolated margin-note fragments
        if line in {"suspect.", "question;", "question.", "are"}:
            i += 1
            continue

        cleaned.append(line)
        i += 1

    # second pass: collapse duplicated adjacent lines
    deduped: list[str] = []
    for line in cleaned:
        if deduped and deduped[-1] == line:
            continue
        deduped.append(line)

    return "\n".join(deduped).strip()