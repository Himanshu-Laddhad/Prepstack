"""
Resume review helpers — Python equivalent of lib/resume-review.ts
"""

from __future__ import annotations

import re
from typing import Any

from lib.types import (
    ResumeAgentReview,
    ResumeFeedback,
    ResumeReviewLogEntry,
    ResumeReviewState,
    ResumeScoreBreakdown,
    ResumeScoreBreakdownDimension,
    ResumeScores,
    ResumeSectionBlock,
    ResumeSectionFeedback,
    ResumeSuggestion,
    SectionFeedback,
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _sanitize_line(line: str) -> str:
    return re.sub(r"\s+", " ", line).strip()


def _chunk_content(text: str, max_lines: int = 6) -> str:
    lines = [_sanitize_line(l) for l in text.split("\n") if _sanitize_line(l)]
    if len(lines) <= max_lines:
        return "\n".join(lines)
    return "\n".join(lines[:max_lines])


def _infer_kind(title: str) -> str:
    normalized = title.lower()
    if "summary" in normalized or "profile" in normalized:
        return "summary"
    if "experience" in normalized:
        return "experience"
    if "education" in normalized:
        return "education"
    if "skill" in normalized:
        return "skills"
    if "project" in normalized:
        return "projects"
    return "other"


def _normalize_factor_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _normalize_score_breakdown_dimension(
    source: Any,
    fallback_score: int,
    valid_suggestion_ids: set[str],
) -> ResumeScoreBreakdownDimension:
    if not isinstance(source, dict):
        source = {}
    return ResumeScoreBreakdownDimension(
        score=source.get("score", fallback_score) if isinstance(source.get("score"), int) else fallback_score,
        summary=source.get("summary", "").strip() if isinstance(source.get("summary"), str) else "",
        positiveFactors=_normalize_factor_list(source.get("positiveFactors")),
        negativeFactors=_normalize_factor_list(source.get("negativeFactors")),
        relatedSuggestionIds=[
            sid for sid in _normalize_factor_list(source.get("relatedSuggestionIds"))
            if sid in valid_suggestion_ids
        ],
    )


def _normalize_score_breakdown(
    source: Any,
    scores: ResumeScores,
    suggestions: list[ResumeSuggestion],
) -> ResumeScoreBreakdown:
    if not isinstance(source, dict):
        source = {}
    valid_ids = {s.id for s in suggestions}
    return ResumeScoreBreakdown(
        impact=_normalize_score_breakdown_dimension(source.get("impact"), scores.impact, valid_ids),
        clarity=_normalize_score_breakdown_dimension(source.get("clarity"), scores.clarity, valid_ids),
        atsCompatibility=_normalize_score_breakdown_dimension(
            source.get("atsCompatibility"), scores.atsCompatibility, valid_ids
        ),
        buzzwordDensity=_normalize_score_breakdown_dimension(
            source.get("buzzwordDensity"), scores.buzzwordDensity, valid_ids
        ),
    )


def _coerce_suggestion(
    raw: dict[str, Any],
    index: int,
    fallback_section_id: str,
) -> ResumeSuggestion:
    priority_raw = raw.get("priority", "")
    priority = priority_raw if priority_raw in ("high", "medium", "low") else ("high" if index == 0 else "medium")
    return ResumeSuggestion(
        id=(raw.get("id") or "").strip() or f"suggestion-{index + 1}",
        title=(raw.get("title") or "").strip() or f"Suggestion {index + 1}",
        targetSectionId=(raw.get("targetSectionId") or "").strip() or fallback_section_id,
        priority=priority,
        originalText=(raw.get("originalText") or "").strip() or None,
        rationale=(raw.get("rationale") or "").strip() or "This change would make the section easier to understand.",
        recommendation=(raw.get("recommendation") or "").strip() or "Revise this section to make the point more concrete.",
        draftRewrite=(raw.get("draftRewrite") or "").strip() or "Rewrite this line with stronger, more specific language.",
    )


def _fallback_section_feedback() -> ResumeSectionFeedback:
    return ResumeSectionFeedback(
        summary=SectionFeedback(present=False, feedback="No summary feedback generated yet."),
        experience=SectionFeedback(present=False, feedback="No experience feedback generated yet.", highlights=[]),
        education=SectionFeedback(present=False, feedback="No education feedback generated yet."),
        skills=SectionFeedback(present=False, feedback="No skills feedback generated yet."),
        projects=SectionFeedback(present=False, feedback="No projects feedback generated yet."),
    )


# ---------------------------------------------------------------------------
# Public API (mirrors lib/resume-review.ts exports)
# ---------------------------------------------------------------------------

def build_resume_sections(raw_text: str) -> list[ResumeSectionBlock]:
    normalized = (raw_text or "").replace("\r", "")
    pattern = r"^(summary|professional summary|experience|work experience|education|skills|projects)\s*$"
    headings = list(re.finditer(pattern, normalized, re.IGNORECASE | re.MULTILINE))

    if not headings:
        return [
            ResumeSectionBlock(
                id="resume-overview",
                title="Resume Overview",
                kind="other",
                content=_chunk_content(normalized, 14),
            )
        ]

    sections: list[ResumeSectionBlock] = []
    for i, match in enumerate(headings):
        title = _sanitize_line(match.group(0))
        start = match.start() + len(match.group(0))
        end = headings[i + 1].start() if i + 1 < len(headings) else len(normalized)
        content = _chunk_content(normalized[start:end].strip(), 10)
        if not content:
            continue
        section_id = re.sub(r"[^a-z0-9]+", "-", title.lower())
        sections.append(
            ResumeSectionBlock(id=section_id, title=title, kind=_infer_kind(title), content=content)
        )

    if sections:
        return sections
    return [
        ResumeSectionBlock(
            id="resume-overview",
            title="Resume Overview",
            kind="other",
            content=_chunk_content(normalized, 14),
        )
    ]


def normalize_resume_review(source: Any, raw_text: str) -> ResumeAgentReview:
    if not isinstance(source, dict):
        source = {}

    # Resume sections
    raw_sections = source.get("resumeSections")
    if isinstance(raw_sections, list) and raw_sections:
        resume_sections = [
            ResumeSectionBlock(
                id=(s.get("id") or "").strip() or f"section-{i + 1}",
                title=(s.get("title") or "").strip() or f"Section {i + 1}",
                kind=s.get("kind") or _infer_kind(s.get("title") or ""),
                content=(s.get("content") or "").strip(),
            )
            for i, s in enumerate(raw_sections)
            if isinstance(s, dict) and (s.get("content") or "").strip()
        ]
    else:
        resume_sections = build_resume_sections(raw_text)

    primary_section_id = resume_sections[0].id if resume_sections else "resume-overview"

    # Suggestions
    raw_suggestions = source.get("suggestions")
    if isinstance(raw_suggestions, list) and raw_suggestions:
        suggestions = [
            _coerce_suggestion(s, i, primary_section_id)
            for i, s in enumerate(raw_suggestions)
            if isinstance(s, dict)
        ]
    else:
        top_fixes = source.get("topFixes") or []
        suggestions = [
            _coerce_suggestion(
                {
                    "id": f"suggestion-{i + 1}",
                    "title": f"Fix {i + 1}",
                    "targetSectionId": primary_section_id,
                    "priority": "high" if i == 0 else "medium",
                    "rationale": "This was flagged as one of the highest-impact improvements.",
                    "recommendation": fix,
                    "draftRewrite": f"Rewrite this area to address: {fix}",
                },
                i,
                primary_section_id,
            )
            for i, fix in enumerate(top_fixes)
            if isinstance(fix, str)
        ]

    # Scores
    raw_scores = source.get("scores") or {}
    scores = ResumeScores(
        impact=raw_scores.get("impact", 0),
        clarity=raw_scores.get("clarity", 0),
        atsCompatibility=raw_scores.get("atsCompatibility", 0),
        buzzwordDensity=raw_scores.get("buzzwordDensity", 0),
    )

    # Section feedback
    fallback_sf = _fallback_section_feedback()
    raw_sf = source.get("sectionFeedback") or {}

    def _merge_section(key: str, default: SectionFeedback) -> SectionFeedback:
        raw = raw_sf.get(key)
        if not isinstance(raw, dict):
            return default
        highlights = raw.get("highlights") if key == "experience" else None
        return SectionFeedback(
            present=bool(raw.get("present", default.present)),
            feedback=str(raw.get("feedback", default.feedback)),
            highlights=highlights if isinstance(highlights, list) else ([] if key == "experience" else None),
        )

    section_feedback = ResumeSectionFeedback(
        summary=_merge_section("summary", fallback_sf.summary),
        experience=_merge_section("experience", fallback_sf.experience),
        education=_merge_section("education", fallback_sf.education),
        skills=_merge_section("skills", fallback_sf.skills),
        projects=_merge_section("projects", fallback_sf.projects),
    )

    return ResumeAgentReview(
        scores=scores,
        scoreBreakdown=_normalize_score_breakdown(source.get("scoreBreakdown"), scores, suggestions),
        sectionFeedback=section_feedback,
        topFixes=source.get("topFixes", []) if isinstance(source.get("topFixes"), list) else [],
        keywordsDetected=source.get("keywordsDetected", []) if isinstance(source.get("keywordsDetected"), list) else [],
        keywordsMissing=source.get("keywordsMissing", []) if isinstance(source.get("keywordsMissing"), list) else [],
        summary=(source.get("summary") or "Review complete.").strip(),
        resumeSections=resume_sections,
        suggestions=suggestions,
    )


def extract_review_state(parsed_json: Any) -> ResumeReviewState:
    if not isinstance(parsed_json, dict):
        return ResumeReviewState(suggestionLog=[])
    review_state = parsed_json.get("reviewState") or {}
    raw_log = review_state.get("suggestionLog") if isinstance(review_state, dict) else []
    if not isinstance(raw_log, list):
        return ResumeReviewState(suggestionLog=[])
    entries = [
        ResumeReviewLogEntry(
            suggestionId=entry.get("suggestionId", ""),
            status=entry.get("status", "pending"),
            thread=entry.get("thread", []),
            title=entry.get("title"),
            recommendation=entry.get("recommendation"),
            draftRewrite=entry.get("draftRewrite"),
        )
        for entry in raw_log
        if isinstance(entry, dict)
    ]
    return ResumeReviewState(suggestionLog=entries)


def build_initial_suggestion_log(
    suggestions: list[ResumeSuggestion],
    existing: list[ResumeReviewLogEntry],
) -> list[ResumeReviewLogEntry]:
    existing_by_id = {e.suggestionId: e for e in existing}
    return [
        ResumeReviewLogEntry(
            suggestionId=s.id,
            status=existing_by_id[s.id].status if s.id in existing_by_id else "pending",
            thread=existing_by_id[s.id].thread if s.id in existing_by_id else [],
            title=existing_by_id[s.id].title if s.id in existing_by_id else s.title,
            recommendation=existing_by_id[s.id].recommendation if s.id in existing_by_id else s.recommendation,
            draftRewrite=existing_by_id[s.id].draftRewrite if s.id in existing_by_id else s.draftRewrite,
        )
        for s in suggestions
    ]


def upsert_suggestion_log_entry(
    existing: list[ResumeReviewLogEntry],
    entry: ResumeReviewLogEntry,
) -> list[ResumeReviewLogEntry]:
    remaining = [e for e in existing if e.suggestionId != entry.suggestionId]
    return [entry, *remaining]


def build_suggestion_log_entry(
    state: ResumeReviewState,
    suggestion: ResumeSuggestion,
    status: str,
    thread: list | None = None,
) -> ResumeReviewLogEntry:
    prior = next((e for e in state.suggestionLog if e.suggestionId == suggestion.id), None)
    return ResumeReviewLogEntry(
        suggestionId=suggestion.id,
        status=status,
        thread=thread if thread is not None else (prior.thread if prior else []),
        title=suggestion.title,
        recommendation=suggestion.recommendation,
        draftRewrite=suggestion.draftRewrite,
    )
