import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.db.session import engine
from app.db.base import Base

# Import models so SQLAlchemy knows about them
from app.models.case_law import LegalCase, LegalCaseChunk  # noqa: F401


def main() -> None:
    Base.metadata.create_all(bind=engine)
    print("Case law tables created successfully.")


if __name__ == "__main__":
    main()