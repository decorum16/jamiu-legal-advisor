from fastapi import FastAPI

from app.api.routes.ask import router as ask_router
from app.api.routes.legal_search import router as legal_search_router
from app.api.routes.legal_answer import router as legal_answer_router

from app.core.database import engine, Base

app = FastAPI()

# 🔥 THIS LINE FIXES YOUR ERROR
Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"name": "Jamiu Legal Advisor Nigeria"}

app = FastAPI(
    title="Jamiu Legal Advisor",
    version="1.0.0",
)

app.include_router(ask_router, prefix="/api/v1")
app.include_router(legal_search_router, prefix="/api/v1")
app.include_router(legal_answer_router, prefix="/api/v1")


@app.get("/")
def root() -> dict[str, str | list[str]]:
    return {
        "name": "Jamiu Legal Advisor Nigeria",
        "scope": "Nigeria",
        "modes": ["nls_student", "lawyer", "police"],
    }


@app.get("/api/v1/health")
def health():
    return {
        "status": "ok",
        "service": "jamiu-api",
        "country": "Nigeria",
        "database": "connected",
    }