"""
SQLAlchemy models using SQLite-compatible types.
JSON columns use the generic sqlalchemy.types.JSON (stored as text in SQLite).
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.types import JSON
from sqlalchemy.orm import relationship

from database import Base


def _gen_id() -> str:
    return uuid.uuid4().hex[:25]


class User(Base):
    __tablename__ = "User"

    id            = Column(String, primary_key=True, default=_gen_id)
    email         = Column(String, unique=True, nullable=False)
    name          = Column(String, nullable=True)
    avatarUrl     = Column(String, nullable=True)
    targetRole    = Column(String, nullable=True)
    preferredVoice = Column(String, nullable=False, default="alex")
    createdAt     = Column(DateTime, nullable=False, default=datetime.utcnow)

    sessions = relationship("InterviewSession", back_populates="user", cascade="all, delete-orphan")
    resumes  = relationship("Resume",           back_populates="user", cascade="all, delete-orphan")


class Resume(Base):
    __tablename__ = "Resume"

    id           = Column(String, primary_key=True, default=_gen_id)
    userId       = Column(String, ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    label        = Column(String, nullable=True)
    rawText      = Column(Text,   nullable=False, default="")
    parsedJson   = Column(JSON,   nullable=False, default=dict)
    fileUrl      = Column(String, nullable=False, default="")
    isActive     = Column(Boolean, nullable=False, default=False)
    impactScore  = Column(Integer, nullable=True)
    clarityScore = Column(Integer, nullable=True)
    atsScore     = Column(Integer, nullable=True)
    buzzwordScore = Column(Integer, nullable=True)
    feedbackJson = Column(JSON, nullable=True)
    createdAt    = Column(DateTime, nullable=False, default=datetime.utcnow)

    sessions = relationship("InterviewSession", back_populates="resume")
    user     = relationship("User", back_populates="resumes")


class InterviewSession(Base):
    __tablename__ = "InterviewSession"

    id                    = Column(String,  primary_key=True, default=_gen_id)
    userId                = Column(String,  ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    resumeId              = Column(String,  ForeignKey("Resume.id"), nullable=True)
    mode                  = Column(String,  nullable=False)   # BEHAVIORAL | TECHNICAL | CASE | STRESS
    persona               = Column(String,  nullable=False, default="alex")
    targetRole            = Column(String,  nullable=True)
    targetDurationMinutes = Column(Integer, nullable=False, default=30)
    transcript            = Column(JSON,    nullable=False, default=list)
    scorecard             = Column(JSON,    nullable=True)
    shareToken            = Column(String,  unique=True, nullable=True)
    startedAt             = Column(DateTime, nullable=False, default=datetime.utcnow)
    endedAt               = Column(DateTime, nullable=True)
    durationSeconds       = Column(Integer, nullable=True)

    user   = relationship("User",   back_populates="sessions")
    resume = relationship("Resume", back_populates="sessions")
