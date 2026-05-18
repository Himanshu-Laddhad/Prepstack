"""
PrepStack — Python/FastAPI

Run:
    uvicorn main:app --reload --port 8000
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import Base, engine
from routers import interview, pages, resume, tts

app = FastAPI(
    title="PrepStack API",
    description="AI-powered mock interview and resume review platform",
    version="1.0.0",
)

# ── Startup: create DB tables ─────────────────────────────────
@app.on_event("startup")
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# ── CORS ──────────────────────────────────────────────────────
_origins = os.environ.get(
    "ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static files ──────────────────────────────────────────────
app.mount("/static",  StaticFiles(directory="static"),  name="static")

_uploads = Path(__file__).parent / "uploads"
_uploads.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(_uploads)), name="uploads")

# ── Routers ───────────────────────────────────────────────────
app.include_router(interview.router)   # /api/interview/*
app.include_router(resume.router)      # /api/resume/*
app.include_router(tts.router)         # /api/tts
app.include_router(pages.router)       # / /interview /resume (HTML pages)

# ── Health ────────────────────────────────────────────────────
@app.get("/api/health")
async def health():
    return {"status": "ok"}
