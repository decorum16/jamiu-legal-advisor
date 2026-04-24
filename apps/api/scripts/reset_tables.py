from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.db.base import Base
from app.db.session import engine
from app.models.legal import LegalSource, LegalChunk


def main():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Tables dropped and recreated successfully")


if __name__ == "__main__":
    main()