"""
Server-side page routes — render Jinja2 templates with DB data.

Uses the Starlette 1.0 TemplateResponse signature:
    templates.TemplateResponse(request, "name.html", context_dict)
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import DEFAULT_USER_ID
from database import get_db
from lib.resume_review import normalize_resume_review
from models import InterviewSession, Resume

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="templates")


@router.get("/")
async def page_home(request: Request):
    return templates.TemplateResponse(request, "index.html")


@router.get("/interview")
async def page_interview_setup(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Resume)
        .where(Resume.userId == DEFAULT_USER_ID)
        .order_by(Resume.createdAt.desc())
    )
    resumes = result.scalars().all()
    return templates.TemplateResponse(
        request, "interview_setup.html", {"active": "interview", "resumes": resumes}
    )


@router.get("/interview/session")
async def page_interview_session(
    request: Request, id: str, db: AsyncSession = Depends(get_db)
):
    session = await db.get(InterviewSession, id)
    if not session:
        return RedirectResponse("/interview")
    return templates.TemplateResponse(
        request, "interview_session.html", {"active": "interview", "session": session}
    )


@router.get("/interview/results")
async def page_interview_results(
    request: Request, id: str, db: AsyncSession = Depends(get_db)
):
    session = await db.get(InterviewSession, id)
    if not session or not session.scorecard:
        return RedirectResponse("/interview")
    return templates.TemplateResponse(
        request,
        "interview_results.html",
        {"active": "interview", "session": session, "scorecard": session.scorecard},
    )


@router.get("/resume")
async def page_resume(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Resume)
        .where(Resume.userId == DEFAULT_USER_ID)
        .order_by(Resume.createdAt.desc())
    )
    resumes = result.scalars().all()
    return templates.TemplateResponse(
        request, "resume.html", {"active": "resume", "resumes": resumes}
    )


@router.get("/resume/review")
async def page_resume_review(
    request: Request, id: str, db: AsyncSession = Depends(get_db)
):
    resume = await db.get(Resume, id)
    if not resume:
        return RedirectResponse("/resume")
    review = (
        normalize_resume_review(resume.feedbackJson, resume.rawText)
        if resume.feedbackJson
        else None
    )
    # Convert Pydantic model to plain dict so Jinja2's tojson filter can serialize it
    review_dict = review.model_dump() if review else None
    return templates.TemplateResponse(
        request,
        "resume_review.html",
        {"active": "resume", "resume": resume, "review": review_dict},
    )
