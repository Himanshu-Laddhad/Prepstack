"""
Resume routes — /api/resume/*

PDFs are stored on local disk under uploads/ instead of Supabase Storage.
"""

import io
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from pypdf import PdfReader
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import MockUser, get_current_user
from database import get_db
from lib.prompts import build_resume_review_prompt
from lib.resume_review import (
    build_initial_suggestion_log,
    build_suggestion_log_entry,
    extract_review_state,
    normalize_resume_review,
    upsert_suggestion_log_entry,
)
from models import Resume, User

router = APIRouter(prefix="/api/resume", tags=["resume"])

UPLOADS_DIR = Path(__file__).parent.parent / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

MAX_RESUME_COUNT = 5
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


def _nvidia_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=os.environ["NVIDIA_API_KEY"],
        base_url="https://integrate.api.nvidia.com/v1",
    )


def _clean_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        nl = text.find("\n")
        if nl != -1:
            text = text[nl + 1:]
        end = text.rfind("```")
        if end != -1:
            text = text[:end]
    return text.strip()


def _extract_pdf_text(file_bytes: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        return ""


async def _ensure_default_user(db: AsyncSession, user: MockUser) -> None:
    existing = await db.get(User, user.id)
    if not existing:
        db.add(User(id=user.id, email=user.email))
        await db.commit()


# ---------------------------------------------------------------------------
# POST /api/resume/upload
# ---------------------------------------------------------------------------

@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    label: str | None = Form(default=None),
    rawText: str | None = Form(default=None),
    user: MockUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename or not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 5MB)")

    result = await db.execute(
        select(func.count()).select_from(Resume).where(Resume.userId == user.id)
    )
    count: int = result.scalar_one()
    if count >= MAX_RESUME_COUNT:
        raise HTTPException(status_code=400, detail="Maximum 5 resumes allowed")

    # Save to local disk under uploads/<timestamp>-<filename>
    timestamp = int(datetime.utcnow().timestamp() * 1000)
    safe_name = f"{timestamp}-{Path(file.filename).name}"
    dest = UPLOADS_DIR / safe_name
    dest.write_bytes(file_bytes)
    file_url = f"/uploads/{safe_name}"

    # Extract text server-side if client didn't send it
    extracted_text = (rawText or "").strip() or _extract_pdf_text(file_bytes)

    await _ensure_default_user(db, user)

    resume = Resume(
        userId=user.id,
        label=label or None,
        rawText=extracted_text,
        parsedJson={},
        fileUrl=file_url,
        isActive=count == 0,
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)

    return {"resumeId": resume.id, "rawText": extracted_text, "fileUrl": file_url}


# ---------------------------------------------------------------------------
# POST /api/resume/review
# ---------------------------------------------------------------------------

class ReviewRequest(BaseModel):
    resumeId: str
    targetRole: str | None = None


@router.post("/review")
async def review_resume(
    body: ReviewRequest,
    user: MockUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not os.environ.get("NVIDIA_API_KEY"):
        raise HTTPException(status_code=503, detail="AI service is not configured.")

    result = await db.execute(
        select(Resume).where(Resume.id == body.resumeId, Resume.userId == user.id)
    )
    resume: Resume | None = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    prompt = build_resume_review_prompt(resume.rawText, body.targetRole)

    client = _nvidia_client()
    response = await client.chat.completions.create(
        model="meta/llama-3.3-70b-instruct",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    response_text = response.choices[0].message.content or ""

    try:
        raw = json.loads(_clean_json(response_text))
        feedback = normalize_resume_review(raw, resume.rawText)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to parse AI response") from exc

    existing_state = extract_review_state(resume.parsedJson)
    suggestion_log = build_initial_suggestion_log(feedback.suggestions, existing_state.suggestionLog)

    resume.impactScore = feedback.scores.impact
    resume.clarityScore = feedback.scores.clarity
    resume.atsScore = feedback.scores.atsCompatibility
    resume.buzzwordScore = feedback.scores.buzzwordDensity
    resume.feedbackJson = feedback.model_dump()
    resume.parsedJson = {
        "reviewState": {"suggestionLog": [e.model_dump() for e in suggestion_log]}
    }
    await db.commit()

    return feedback.model_dump()


# ---------------------------------------------------------------------------
# POST /api/resume/review/question
# ---------------------------------------------------------------------------

class QuestionRequest(BaseModel):
    resumeId: str
    suggestionId: str
    question: str = Field(min_length=1)


@router.post("/review/question")
async def question_resume(
    body: QuestionRequest,
    user: MockUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not os.environ.get("NVIDIA_API_KEY"):
        raise HTTPException(status_code=503, detail="AI service is not configured.")

    result = await db.execute(
        select(Resume).where(Resume.id == body.resumeId, Resume.userId == user.id)
    )
    resume: Resume | None = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    review = normalize_resume_review(resume.feedbackJson, resume.rawText)
    suggestion = next((s for s in review.suggestions if s.id == body.suggestionId), None)
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    client = _nvidia_client()
    response = await client.chat.completions.create(
        model="meta/llama-3.3-70b-instruct",
        max_tokens=300,
        messages=[{
            "role": "user",
            "content": (
                "You are answering a focused follow-up question about one resume suggestion.\n\n"
                f"Resume excerpt:\n{resume.rawText[:2500]}\n\n"
                f"Suggestion title: {suggestion.title}\n"
                f"Original wording: {suggestion.originalText or 'Not provided'}\n"
                f"Suggestion rationale: {suggestion.rationale}\n"
                f"Suggestion recommendation: {suggestion.recommendation}\n"
                f"Draft rewrite: {suggestion.draftRewrite}\n\n"
                f"User question: {body.question}\n\n"
                "Respond in 2-4 sentences. Stay specific to this suggestion. Do not use markdown."
            ),
        }],
    )
    answer = (response.choices[0].message.content or "").strip() or (
        "I would make this change because it makes the section more concrete and easier to scan."
    )

    state = extract_review_state(resume.parsedJson)
    prior = next((e for e in state.suggestionLog if e.suggestionId == suggestion.id), None)
    log_entry = build_suggestion_log_entry(
        state=state,
        suggestion=suggestion,
        status="questioned",
        thread=[
            *(prior.thread if prior else []),
            {"role": "user", "content": body.question},
            {"role": "assistant", "content": answer},
        ],
    )
    resume.parsedJson = {
        "reviewState": {
            "suggestionLog": [
                e.model_dump()
                for e in upsert_suggestion_log_entry(state.suggestionLog, log_entry)
            ]
        }
    }
    await db.commit()

    return {"answer": answer, "logEntry": log_entry.model_dump()}


# ---------------------------------------------------------------------------
# POST /api/resume/review/agree
# ---------------------------------------------------------------------------

class AgreeRequest(BaseModel):
    resumeId: str
    suggestionId: str


@router.post("/review/agree")
async def agree_resume(
    body: AgreeRequest,
    user: MockUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Resume).where(Resume.id == body.resumeId, Resume.userId == user.id)
    )
    resume: Resume | None = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    review = normalize_resume_review(resume.feedbackJson, resume.rawText)
    suggestion = next((s for s in review.suggestions if s.id == body.suggestionId), None)
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    state = extract_review_state(resume.parsedJson)
    log_entry = build_suggestion_log_entry(state=state, suggestion=suggestion, status="accepted")
    resume.parsedJson = {
        "reviewState": {
            "suggestionLog": [
                e.model_dump()
                for e in upsert_suggestion_log_entry(state.suggestionLog, log_entry)
            ]
        }
    }
    await db.commit()
    return {"logEntry": log_entry.model_dump()}


# ---------------------------------------------------------------------------
# POST /api/resume/review/skip
# ---------------------------------------------------------------------------

class SkipRequest(BaseModel):
    resumeId: str
    suggestionId: str


@router.post("/review/skip")
async def skip_resume(
    body: SkipRequest,
    user: MockUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Resume).where(Resume.id == body.resumeId, Resume.userId == user.id)
    )
    resume: Resume | None = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    review = normalize_resume_review(resume.feedbackJson, resume.rawText)
    suggestion = next((s for s in review.suggestions if s.id == body.suggestionId), None)
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    state = extract_review_state(resume.parsedJson)
    log_entry = build_suggestion_log_entry(state=state, suggestion=suggestion, status="skipped")
    resume.parsedJson = {
        "reviewState": {
            "suggestionLog": [
                e.model_dump()
                for e in upsert_suggestion_log_entry(state.suggestionLog, log_entry)
            ]
        }
    }
    await db.commit()
    return {"logEntry": log_entry.model_dump()}


# ---------------------------------------------------------------------------
# POST /api/resume/activate
# ---------------------------------------------------------------------------

class ActivateRequest(BaseModel):
    resumeId: str


@router.post("/activate")
async def activate_resume(
    body: ActivateRequest,
    user: MockUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Resume).where(Resume.userId == user.id))
    all_resumes: list[Resume] = result.scalars().all()

    target = next((r for r in all_resumes if r.id == body.resumeId), None)
    if not target:
        raise HTTPException(status_code=404, detail="Resume not found")

    for r in all_resumes:
        r.isActive = r.id == body.resumeId
    await db.commit()
    return {"success": True}


# ---------------------------------------------------------------------------
# DELETE /api/resume/{id}
# ---------------------------------------------------------------------------

@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: str,
    user: MockUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not resume_id or len(resume_id) > 50:
        raise HTTPException(status_code=400, detail="Invalid resume id")

    result = await db.execute(
        select(Resume).where(Resume.id == resume_id, Resume.userId == user.id)
    )
    resume: Resume | None = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    # Delete local file
    if resume.fileUrl and resume.fileUrl.startswith("/uploads/"):
        local_path = UPLOADS_DIR / resume.fileUrl.removeprefix("/uploads/")
        try:
            local_path.unlink(missing_ok=True)
        except Exception:
            pass

    was_active = resume.isActive
    await db.delete(resume)
    await db.flush()

    if was_active:
        next_result = await db.execute(
            select(Resume)
            .where(Resume.userId == user.id)
            .order_by(Resume.createdAt.desc())
            .limit(1)
        )
        next_resume: Resume | None = next_result.scalar_one_or_none()
        if next_resume:
            next_resume.isActive = True

    await db.commit()
    return {"success": True}
