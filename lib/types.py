"""
Pydantic types — Python equivalent of lib/types.ts
"""

from __future__ import annotations

from typing import Any, Literal, Optional
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Enums / literals
# ---------------------------------------------------------------------------

InterviewMode = Literal["BEHAVIORAL", "TECHNICAL", "CASE", "STRESS"]
PersonaId = Literal["alex", "terry", "frankie", "panel"]


# ---------------------------------------------------------------------------
# Interview / transcript
# ---------------------------------------------------------------------------

class TranscriptMessage(BaseModel):
    role: Literal["assistant", "user"]
    content: str
    timestamp: str


# ---------------------------------------------------------------------------
# Resume scores
# ---------------------------------------------------------------------------

class ResumeScores(BaseModel):
    impact: int
    clarity: int
    atsCompatibility: int
    buzzwordDensity: int


class ResumeScoreBreakdownDimension(BaseModel):
    score: int
    summary: str
    positiveFactors: list[str]
    negativeFactors: list[str]
    relatedSuggestionIds: list[str]


class ResumeScoreBreakdown(BaseModel):
    impact: ResumeScoreBreakdownDimension
    clarity: ResumeScoreBreakdownDimension
    atsCompatibility: ResumeScoreBreakdownDimension
    buzzwordDensity: ResumeScoreBreakdownDimension


class SectionFeedback(BaseModel):
    present: bool
    feedback: str
    highlights: Optional[list[str]] = None


class ResumeSectionFeedback(BaseModel):
    summary: SectionFeedback
    experience: SectionFeedback
    education: SectionFeedback
    skills: SectionFeedback
    projects: SectionFeedback


class ResumeFeedback(BaseModel):
    scores: ResumeScores
    scoreBreakdown: ResumeScoreBreakdown
    sectionFeedback: ResumeSectionFeedback
    topFixes: list[str]
    keywordsDetected: list[str]
    keywordsMissing: list[str]
    summary: str


ResumeSectionKind = Literal["summary", "experience", "education", "skills", "projects", "other"]


class ResumeSectionBlock(BaseModel):
    id: str
    title: str
    kind: ResumeSectionKind
    content: str


class ResumeSuggestion(BaseModel):
    id: str
    title: str
    targetSectionId: str
    priority: Literal["high", "medium", "low"]
    originalText: Optional[str] = None
    rationale: str
    recommendation: str
    draftRewrite: str


class ResumeAgentReview(ResumeFeedback):
    resumeSections: list[ResumeSectionBlock]
    suggestions: list[ResumeSuggestion]


# ---------------------------------------------------------------------------
# Resume review state (wizard log)
# ---------------------------------------------------------------------------

class ResumeReviewThreadMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ResumeReviewLogEntry(BaseModel):
    suggestionId: str
    status: Literal["pending", "accepted", "questioned", "skipped"]
    thread: list[ResumeReviewThreadMessage]
    title: Optional[str] = None
    recommendation: Optional[str] = None
    draftRewrite: Optional[str] = None


class ResumeReviewState(BaseModel):
    suggestionLog: list[ResumeReviewLogEntry]


# ---------------------------------------------------------------------------
# Interview scorecard
# ---------------------------------------------------------------------------

class ScorecardDimension(BaseModel):
    score: int
    note: str


class ScorecardDimensions(BaseModel):
    communicationClarity: ScorecardDimension
    relevance: ScorecardDimension
    starAdherence: Optional[ScorecardDimension] = None
    resumeAlignment: ScorecardDimension
    confidenceProxy: ScorecardDimension


class Scorecard(BaseModel):
    overallScore: int
    dimensions: ScorecardDimensions
    strengths: list[str]
    improvements: list[str]
    standoutMoment: str
    summary: str


# ---------------------------------------------------------------------------
# Personas
# ---------------------------------------------------------------------------

class Persona(BaseModel):
    id: PersonaId
    name: str
    description: str
    tone: str
    instructions: str


class InterviewModeConfig(BaseModel):
    id: InterviewMode
    label: str
    description: str
    questionStyle: str
