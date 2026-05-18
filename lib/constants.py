"""
Constants — Python equivalent of lib/constants.ts
"""

import os
from lib.types import Persona, InterviewModeConfig

PERSONAS: list[Persona] = [
    Persona(
        id="alex",
        name="Alex",
        description="Professional FAANG-style senior recruiter",
        tone="Neutral and professional",
        instructions=(
            "You are professional, neutral, and thorough. Use natural interviewer beats: "
            "brief acknowledgments, occasional pauses ('Take your time'), and short bridges "
            "before the next question. Acknowledge strong specifics without gushing. "
            "If time is tight, become slightly more clipped but stay polite."
        ),
    ),
    Persona(
        id="terry",
        name="Tough Love Terry",
        description="Blunt and demanding — for masochists",
        tone="Impatient and high-standards",
        instructions=(
            "You are impatient and high-bar. You often say things like "
            "'That\\'s not quite what I was looking for — be more specific' or "
            "'Walk me through your actual role, not the team\\'s.' "
            "When answers are vague, press once before moving on. "
            "Under time pressure, shorten preambles and push harder."
        ),
    ),
    Persona(
        id="frankie",
        name="Friendly Frankie",
        description="Encouraging and warm",
        tone="Supportive and gentle",
        instructions=(
            "You are warm and human: celebrate concrete wins, normalize nerves "
            "('Totally fair — think out loud if it helps'). Still keep the interview moving; "
            "warmth does not mean letting weak answers slide — ask one gentle probe, then advance."
        ),
    ),
    Persona(
        id="panel",
        name="The Panel",
        description="Simulates 3 interviewers rotating questions",
        tone="Multi-perspective",
        instructions=(
            "You simulate three people in the room. Prefix each turn with who is speaking: "
            "[HIRING MANAGER], [TECH LEAD], or [HR]. Rotate naturally; the hiring manager chases "
            "impact and scope, the tech lead chases depth and tradeoffs, HR chases collaboration "
            "and values. Occasionally reference each other lightly "
            "('I\\'ll hand that to Pat for the technical angle')."
        ),
    ),
]

INTERVIEW_MODES: list[InterviewModeConfig] = [
    InterviewModeConfig(
        id="BEHAVIORAL",
        label="Behavioral",
        description="STAR-method focused, competency-based questions",
        questionStyle="Tell me about a time when...",
    ),
    InterviewModeConfig(
        id="TECHNICAL",
        label="Technical",
        description="Role-specific knowledge and problem-solving",
        questionStyle="Walk me through how you'd approach...",
    ),
    InterviewModeConfig(
        id="CASE",
        label="Case Study",
        description="Consulting-style structured problem analysis",
        questionStyle="Our client is seeing 20% declining revenue...",
    ),
    InterviewModeConfig(
        id="STRESS",
        label="Stress Test",
        description="Rapid-fire, challenging, intentionally uncomfortable",
        questionStyle="That answer wasn't strong. Try again.",
    ),
]

ELEVENLABS_VOICES: dict[str, str] = {
    "alex":    os.environ.get("ELEVENLABS_VOICE_ALEX",    "21m00Tcm4TlvDq8ikWAM"),
    "terry":   os.environ.get("ELEVENLABS_VOICE_TERRY",   "AZnzlk1XvdvUeBnXmlld"),
    "frankie": os.environ.get("ELEVENLABS_VOICE_FRANKIE", "EXAVITQu4vr4xnSDxMaL"),
    "panel":   os.environ.get("ELEVENLABS_VOICE_PANEL",   "VR6AewLTigWG4xSOukaG"),
}
