from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.services.ingestion.acja_parser import parse_acja_text


def main() -> None:
    input_path = PROJECT_ROOT / "Legal_sources" / "acja_2015.txt"
    output_path = PROJECT_ROOT / "data" / "acja_parsed_preview.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Using file: {input_path}")

    raw_text = input_path.read_text(encoding="utf-8")
    chunks = parse_acja_text(raw_text)

    preview = [chunk.to_dict() for chunk in chunks[:20]]

    output_path.write_text(
        json.dumps(preview, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Total chunks parsed: {len(chunks)}")
    print(f"Preview written to: {output_path}")

    for idx, chunk in enumerate(chunks[:10], start=1):
        print("=" * 80)
        print(f"Chunk {idx}")
        print(f"part_label     : {chunk.part_label}")
        print(f"section_number : {chunk.section_number}")
        print(f"section_title  : {chunk.section_title}")
        print(f"side_note      : {chunk.side_note}")
        print(f"content_type   : {chunk.content_type}")
        print("text preview   :")
        print(chunk.text[:500])
        print()


if __name__ == "__main__":
    main()