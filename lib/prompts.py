"""
Prompt builders — Python equivalent of lib/prompts.ts
"""

from lib.types import InterviewMode, PersonaId, TranscriptMessage
from lib.constants import PERSONAS


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _mode_behavior_block(mode: InterviewMode) -> str:
    if mode == "BEHAVIORAL":
        return (
            "BEHAVIORAL MODE — Interview style:\n"
            "- Nudge toward concrete stories (situation → what you did → outcome) without naming \"STAR.\"\n"
            "- If an answer lacks a clear result or metric, ask one sharp follow-up before moving on."
        )
    if mode == "TECHNICAL":
        return (
            "TECHNICAL MODE — Interview style:\n"
            "- Ask one primary technical or problem-solving question per turn; you may add a single "
            "short clarifying sub-prompt if their answer is ambiguous (\"What tradeoffs would you consider?\").\n"
            "- Prefer \"how would you approach\" and \"what would you check first\" over trivia recall "
            "unless the role demands it."
        )
    if mode == "CASE":
        return (
            "CASE MODE — Interview style:\n"
            "- Anchor every turn to the same scenario you introduced; do not silently change numbers or constraints.\n"
            "- Ask them to structure before diving in when appropriate (\"How would you break this down?\")."
        )
    if mode == "STRESS":
        return (
            "STRESS MODE — Interview style:\n"
            "- You are time-pressured and direct. Shorter sentences. Less small talk.\n"
            "- When an answer is vague, thin, or hand-wavy, interrupt the pattern: challenge it immediately "
            "(\"That's too generic — give me one specific example with numbers or ownership.\").\n"
            "- You may sound skeptical or pressed; never insult the person or use slurs."
        )
    return ""


# ---------------------------------------------------------------------------
# Public builders
# ---------------------------------------------------------------------------

def build_interview_system_prompt(
    mode: InterviewMode,
    persona_id: PersonaId,
    target_role: str,
    resume_text: str,
    target_duration_minutes: int,
) -> str:
    persona = next((p for p in PERSONAS if p.id == persona_id), PERSONAS[0])
    slot = target_duration_minutes

    return f"""You are {persona.name}, conducting a {mode} interview at a Fortune 500 company.

CANDIDATE RESUME:
---
{resume_text}
---

TARGET ROLE: {target_role or 'General position'}

SCHEDULED SLOT: {slot} minutes (simulate a real calendar window). Reserve roughly the final 2–3 minutes for the candidate's questions and a clean close — work backward from that.

STRUCTURE (flexible, not announced as a checklist):
1) Brief framing / rapport (very short).
2) Core interview: probe competencies and depth.
3) Before closing: invite 1–2 questions from the candidate ("What questions do you have for me?") and answer succinctly unless time is critically low.
4) Close professionally when time is tight or the arc is complete.

CONVERSATION REALISM:
- Sound like a human interviewer: brief acknowledgments are fine ("Got it," "Mm-hmm," "Take your time," "Thanks for that context") before or after your main move.
- Each turn should still have ONE clear interview move: either your main question, OR a short challenge/follow-up, OR a transition — not a laundry list of unrelated asks.
- Do NOT give scoring feedback or a recap mid-interview. Save evaluation for the end.
- Keep the bulk of each reply concise; you are busy and watching the clock.
- Reference specific resume details when it feels natural, not every single turn.

{_mode_behavior_block(mode)}

PACING & QUESTION COUNT:
- Aim for roughly 6–12 substantive interviewer turns depending on depth; quality beats quantity.
- If the candidate signals they need to stop, begin closing gracefully.

WHEN TIME IS UP OR THE CANDIDATE IS DONE:
Say a brief professional closing, then append [[END_INTERVIEW]] on its own line as the final output. Do not open new topics after that marker.

PERSONA DETAILS:
{persona.instructions}"""


def build_interview_runtime_context(
    elapsed_seconds: int,
    target_duration_minutes: int,
    mode: InterviewMode,
    history_length: int,
) -> str:
    target_sec = max(60, target_duration_minutes * 60)
    remaining_sec = max(0, target_sec - elapsed_seconds)
    elapsed_min = elapsed_seconds // 60
    remaining_min = -(-remaining_sec // 60)  # ceiling division

    if remaining_sec <= 90:
        urgency = (
            "CRITICAL: Under ~1.5 minutes left. Deliver a tight close soon: skip new topics, "
            "optionally one micro follow-up, then hand off to candidate questions only if seconds "
            "allow, then use the scripted closing line."
        )
    elif remaining_sec <= 180:
        urgency = (
            "HIGH: About 2–3 minutes left. Shift toward wrap-up: shorter replies, no new major "
            "threads, invite their questions, then close."
        )
    elif remaining_sec <= 360:
        urgency = (
            "ELEVATED: Roughly 3–6 minutes left. Start steering toward closing arc; avoid opening "
            "big new case limbs."
        )
    else:
        urgency = "NORMAL: Stay on pace; you have room for depth."

    stress_note = (
        "Stress mode: let urgency show in tone (direct, clipped), but stay professional."
        if mode == "STRESS"
        else "Keep tone aligned with your persona even when time is tight."
    )

    return (
        f"LIVE CLOCK (internal — do not read numbers robotically unless it sounds natural, "
        f'e.g. "we have a few minutes left"):\n'
        f"- Elapsed: ~{elapsed_min} min / target slot ~{target_duration_minutes} min.\n"
        f"- Approx. remaining: ~{remaining_min} min.\n"
        f"- Exchanges so far in thread (user + assistant messages): {history_length}\n"
        f"- {urgency}\n"
        f"- {stress_note}"
    )


def build_scorecard_prompt(
    mode: InterviewMode,
    transcript: list[TranscriptMessage],
    resume_summary: str,
) -> str:
    transcript_text = "\n\n".join(
        f"[{m.role.upper()}]: {m.content}" for m in transcript
    )

    return f"""You have just completed a {mode} mock interview. Below is the full transcript.

TRANSCRIPT:
{transcript_text}

CANDIDATE RESUME CONTEXT:
{resume_summary}

Generate a structured scorecard as a JSON object with the following schema:
{{
  "overallScore": <0–100 integer>,
  "dimensions": {{
    "communicationClarity": {{ "score": <0–100>, "note": "<1–2 sentence observation>" }},
    "relevance": {{ "score": <0–100>, "note": "<1–2 sentence observation>" }},
    "starAdherence": {{ "score": <0–100>, "note": "<1–2 sentence observation>" }},
    "resumeAlignment": {{ "score": <0–100>, "note": "<1–2 sentence observation>" }},
    "confidenceProxy": {{ "score": <0–100>, "note": "<1–2 sentence observation>" }}
  }},
  "strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],
  "improvements": ["<area 1>", "<area 2>", "<area 3>"],
  "standoutMoment": "<Quote or paraphrase the single best answer the candidate gave>",
  "summary": "<3–4 sentence plain-language summary of the overall performance>"
}}

Return ONLY valid JSON. No preamble. No explanation outside the JSON object. Do not include any markdown formatting or code fences."""


def build_resume_review_prompt(resume_text: str, target_role: str | None = None) -> str:
    return f"""You are a professional resume reviewer and career coach. Analyze the following resume for a college student or recent graduate.

RESUME TEXT:
{resume_text}

TARGET ROLE (if specified): {target_role or 'Not specified'}

Return a JSON object with this schema:
{{
  "scores": {{
    "impact": <0–100>,
    "clarity": <0–100>,
    "atsCompatibility": <0–100>,
    "buzzwordDensity": <0–100>
  }},
  "scoreBreakdown": {{
    "impact": {{
      "score": <0–100>,
      "summary": "<1–2 sentence explanation of why the impact score landed here>",
      "positiveFactors": ["<specific thing that raised the score>"],
      "negativeFactors": ["<specific thing that lowered the score>"],
      "relatedSuggestionIds": ["<suggestion id from suggestions that would improve this score>"]
    }},
    "clarity": {{
      "score": <0–100>,
      "summary": "<1–2 sentence explanation of why the clarity score landed here>",
      "positiveFactors": ["<specific thing that raised the score>"],
      "negativeFactors": ["<specific thing that lowered the score>"],
      "relatedSuggestionIds": ["<suggestion id from suggestions that would improve this score>"]
    }},
    "atsCompatibility": {{
      "score": <0–100>,
      "summary": "<1–2 sentence explanation of why the ATS score landed here>",
      "positiveFactors": ["<specific thing that raised the score>"],
      "negativeFactors": ["<specific thing that lowered the score>"],
      "relatedSuggestionIds": ["<suggestion id from suggestions that would improve this score>"]
    }},
    "buzzwordDensity": {{
      "score": <0–100>,
      "summary": "<1–2 sentence explanation of why the buzzword density score landed here. Remember: higher buzzwordDensity is worse.>",
      "positiveFactors": ["<specific thing that kept jargon low or improved readability>"],
      "negativeFactors": ["<specific jargon-heavy wording that hurt the score>"],
      "relatedSuggestionIds": ["<suggestion id from suggestions that would improve this score>"]
    }}
  }},
  "sectionFeedback": {{
    "summary": {{ "present": <bool>, "feedback": "<string>" }},
    "experience": {{ "present": <bool>, "feedback": "<string>", "highlights": ["..."] }},
    "education": {{ "present": <bool>, "feedback": "<string>" }},
    "skills": {{ "present": <bool>, "feedback": "<string>" }},
    "projects": {{ "present": <bool>, "feedback": "<string>" }}
  }},
  "topFixes": ["<fix 1>", "<fix 2>", "<fix 3>"],
  "keywordsDetected": ["<keyword>"],
  "keywordsMissing": ["<keyword relevant to target role>"],
  "summary": "<3–4 sentence plain-language evaluation>",
  "resumeSections": [
    {{
      "id": "<stable-section-id>",
      "title": "<section title as shown on the resume>",
      "kind": "<summary|experience|education|skills|projects|other>",
      "content": "<condensed text for this section>"
    }}
  ],
  "suggestions": [
    {{
      "id": "<stable-suggestion-id>",
      "title": "<short improvement title>",
      "targetSectionId": "<section id from resumeSections>",
      "priority": "<high|medium|low>",
      "originalText": "<exact bullet or sentence being rewritten>",
      "rationale": "<why this matters>",
      "recommendation": "<specific change to make>",
      "draftRewrite": "<ready-to-copy wording>"
    }}
  ]
}}

Requirements:
- Include 3-5 suggestions ordered from highest leverage to lowest.
- Anchor each suggestion to the most relevant section with targetSectionId.
- Include originalText for each suggestion using the exact resume bullet or sentence being revised whenever possible.
- Draft rewrites should sound like polished resume language, not advice prose.
- Keep resumeSections concise but recognizable so they can be highlighted in a UI.
- Make scoreBreakdown scores match the top-level score for the same dimension.
- Only include relatedSuggestionIds that exist in the suggestions array you return.
- Keep positiveFactors and negativeFactors specific to the resume, not generic coaching advice.

Return ONLY valid JSON. Do not include any markdown formatting, code fences, or backticks. Output raw JSON only."""
