"""
Interview session routes — /api/interview/{start,respond,end}
"""

import json
import os
import secrets
import string
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import MockUser, get_current_user
from database import get_db
from lib.interview_models import get_interview_model
from lib.prompts import (
    build_interview_runtime_context,
    build_interview_system_prompt,
    build_scorecard_prompt,
)
from lib.types import TranscriptMessage
from models import InterviewSession, Resume, User

router = APIRouter(prefix="/api/interview", tags=["interview"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _nanoid(size: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits + "_-"
    return "".join(secrets.choice(alphabet) for _ in range(size))


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


async def _ensure_default_user(db: AsyncSession, user: MockUser) -> None:
    existing = await db.get(User, user.id)
    if not existing:
        db.add(User(id=user.id, email=user.email))
        await db.commit()


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class StartRequest(BaseModel):
    mode: str  # BEHAVIORAL | TECHNICAL | CASE | STRESS
    persona: str = "alex"
    targetRole: str | None = None
    resumeId: str | None = None
    targetDurationMinutes: int = Field(default=30, ge=15, le=60)


class HistoryMessage(BaseModel):
    role: str
    content: str


class RespondRequest(BaseModel):
    sessionId: str
    message: str = Field(min_length=1)
    history: list[HistoryMessage]


class EndTranscriptMessage(BaseModel):
    role: str
    content: str
    timestamp: str


class EndRequest(BaseModel):
    sessionId: str
    transcript: list[EndTranscriptMessage]


# ---------------------------------------------------------------------------
# POST /api/interview/start
# ---------------------------------------------------------------------------

@router.post("/start")
async def start_interview(
    body: StartRequest,
    user: MockUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _ensure_default_user(db, user)

    try:
        session = InterviewSession(
            userId=user.id,
            resumeId=body.resumeId or None,
            mode=body.mode,
            persona=body.persona,
            targetRole=body.targetRole or None,
            targetDurationMinutes=body.targetDurationMinutes,
            transcript=[],
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=503, detail="Database error. Please try again.") from exc

    return {
        "sessionId": session.id,
        "mode": session.mode,
        "persona": session.persona,
        "targetDurationMinutes": session.targetDurationMinutes,
        "startedAt": session.startedAt.isoformat(),
    }


# ---------------------------------------------------------------------------
# POST /api/interview/respond  (streaming)
# ---------------------------------------------------------------------------

@router.post("/respond")
async def respond_interview(
    body: RespondRequest,
    user: MockUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(InterviewSession).where(
            InterviewSession.id == body.sessionId,
            InterviewSession.userId == user.id,
        )
    )
    session: InterviewSession | None = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    resume_text = "No resume provided."
    if session.resumeId:
        resume = await db.get(Resume, session.resumeId)
        if resume:
            resume_text = resume.rawText

    system_prompt = build_interview_system_prompt(
        mode=session.mode,
        persona_id=session.persona,
        target_role=session.targetRole or "General position",
        resume_text=resume_text,
        target_duration_minutes=session.targetDurationMinutes,
    )

    now_utc = datetime.now(timezone.utc)
    started_utc = (
        session.startedAt.replace(tzinfo=timezone.utc)
        if session.startedAt.tzinfo is None
        else session.startedAt
    )
    elapsed_seconds = int((now_utc - started_utc).total_seconds())

    runtime_block = build_interview_runtime_context(
        elapsed_seconds=elapsed_seconds,
        target_duration_minutes=session.targetDurationMinutes,
        mode=session.mode,
        history_length=len(body.history) // 2,
    )
    augmented_system = f"{system_prompt.strip()}\n\n---\n{runtime_block}"

    client = _nvidia_client()

    async def generate():
        stream = await client.chat.completions.create(
            model=get_interview_model("respond"),
            max_tokens=1024,
            messages=[
                {"role": "system", "content": augmented_system},
                *[{"role": m.role, "content": m.content} for m in body.history],
                {"role": "user", "content": body.message},
            ],
            stream=True,
        )
        async for chunk in stream:
            if not chunk.choices:
                continue
            text = chunk.choices[0].delta.content or ""
            if text:
                yield text

    return StreamingResponse(
        generate(),
        media_type="text/plain; charset=utf-8",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ---------------------------------------------------------------------------
# POST /api/interview/end
# ---------------------------------------------------------------------------

@router.post("/end")
async def end_interview(
    body: EndRequest,
    user: MockUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(InterviewSession).where(
            InterviewSession.id == body.sessionId,
            InterviewSession.userId == user.id,
        )
    )
    session: InterviewSession | None = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    resume_text = "No resume provided"
    if session.resumeId:
        resume = await db.get(Resume, session.resumeId)
        if resume and resume.rawText:
            resume_text = resume.rawText[:1000] + "..."

    transcript_messages = [
        TranscriptMessage(role=m.role, content=m.content, timestamp=m.timestamp)
        for m in body.transcript
    ]

    prompt = build_scorecard_prompt(
        mode=session.mode,
        transcript=transcript_messages,
        resume_summary=resume_text,
    )

    client = _nvidia_client()
    response = await client.chat.completions.create(
        model=get_interview_model("end"),
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    response_text = response.choices[0].message.content or "{}"

    try:
        scorecard = json.loads(_clean_json(response_text))
    except json.JSONDecodeError:
        scorecard = {
            "overallScore": 70,
            "summary": "Score generation encountered an error.",
            "strengths": [],
            "improvements": [],
            "dimensions": {},
            "standoutMoment": "",
        }

    share_token = _nanoid(12)
    ended_at = datetime.now(timezone.utc)
    started_utc = (
        session.startedAt.replace(tzinfo=timezone.utc)
        if session.startedAt.tzinfo is None
        else session.startedAt
    )
    duration_seconds = int((ended_at - started_utc).total_seconds())

    session.transcript = [m.model_dump() for m in transcript_messages]
    session.scorecard = scorecard
    session.shareToken = share_token
    session.endedAt = ended_at
    session.durationSeconds = duration_seconds
    await db.commit()

    # Optional email via Resend
    resend_key = os.environ.get("RESEND_API_KEY")
    if resend_key:
        try:
            import resend as resend_lib
            resend_lib.api_key = resend_key
            app_url = os.environ.get("APP_URL", "http://localhost:8000")
            resend_lib.Emails.send({
                "from": os.environ.get("RESEND_FROM_EMAIL", "noreply@prepstack.app"),
                "to": user.email,
                "subject": f"Your PrepStack Interview Report — Score: {scorecard.get('overallScore', '?')}/100",
                "html": (
                    f"<h1>Your Interview Scorecard is Ready!</h1>"
                    f"<p>Overall Score: <strong>{scorecard.get('overallScore', '?')}/100</strong></p>"
                    f"<p>{scorecard.get('summary', '')}</p>"
                    f'<a href="{app_url}/interview/{body.sessionId}/results">View Full Scorecard</a>'
                ),
            })
        except Exception:
            pass

    return {
        "scorecardUrl": f"/interview/{body.sessionId}/results",
        "shareUrl": f"/share/{share_token}",
        "scorecard": scorecard,
    }
