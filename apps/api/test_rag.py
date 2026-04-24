import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

from app.core.database import SessionLocal
from app.services.rag_service import RAGService


def main():
    db = SessionLocal()

    try:
        rag = RAGService(db)

        query = "arrest"

        results = rag.keyword_search(query)

        print(f"\nQuery: {query}\n")

        for r in results:
            print("Citation:", r.citation)
            print("Section:", r.section_label)
            print("Text:", r.text[:200])
            print("----\n")

    finally:
        db.close()


if __name__ == "__main__":
    main()