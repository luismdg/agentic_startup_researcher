from fastapi import FastAPI

from src.api.routes import search

app = FastAPI(title="VC Brain — Agentic Startup Sourcing")
app.include_router(search.router, prefix="/search", tags=["search"])
