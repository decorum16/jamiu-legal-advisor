import json
import re
from pathlib import Path


SOURCE_TITLE = "Constitution of the Federal Republic of Nigeria 1999"
SOURCE_TYPE = "constitution"
JURISDICTION = "federal"


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_noise_lines(lines: list[str]) -> list[str]:
    cleaned = []

    noise_patterns = [
        r"^back to top$",
        r"^nigerian constitution$",
        r"^\d{1,3}$",
    ]

    for line in lines:
        stripped = line.strip()
        if not stripped:
            cleaned.append("")
            continue

        lower = stripped.lower()

        if any(re.match(pattern, lower) for pattern in noise_patterns):
            continue

        cleaned.append(stripped)

    return cleaned


def parse_constitution_chapter_iv(raw_text: str) -> list[dict]:
    text = normalize_text(raw_text)
    lines = clean_noise_lines(text.split("\n"))

    records = []
    current_part_label = "Chapter IV - Fundamental Rights"
    current_section_number = None
    current_side_note = ""
    current_body_lines = []

    section_start_pattern = re.compile(r"^(\d+)\.\s*(.*)$")

    for line in lines:
        if not line:
            if current_section_number is not None:
                current_body_lines.append("")
            continue

        if line.lower() == "chapter iv":
            continue

        if line.lower() == "fundamental rights":
            continue

        match = section_start_pattern.match(line)
        if match:
            if current_section_number is not None:
                records.append(
                    {
                        "source_title": SOURCE_TITLE,
                        "source_type": SOURCE_TYPE,
                        "jurisdiction": JURISDICTION,
                        "part_label": current_part_label,
                        "section_number": str(current_section_number),
                        "side_note": current_side_note,
                        "text": "\n".join(current_body_lines).strip(),
                    }
                )

            current_section_number = match.group(1).strip()
            current_side_note = match.group(2).strip()
            current_body_lines = [line]
            continue

        if current_section_number is not None:
            current_body_lines.append(line)

    if current_section_number is not None:
        records.append(
            {
                "source_title": SOURCE_TITLE,
                "source_type": SOURCE_TYPE,
                "jurisdiction": JURISDICTION,
                "part_label": current_part_label,
                "section_number": str(current_section_number),
                "side_note": current_side_note,
                "text": "\n".join(current_body_lines).strip(),
            }
        )

    return records


def main() -> None:
    input_path = Path("Legal_sources/constitution_chapter_iv_clean.txt")
    output_path = Path("constitution_chapter_iv_parsed.json")

    raw_text = input_path.read_text(encoding="utf-8")
    records = parse_constitution_chapter_iv(raw_text)

    output_path.write_text(
        json.dumps(records, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Parsed {len(records)} sections into {output_path}")


if __name__ == "__main__":
    main()