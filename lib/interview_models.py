"""
Interview model selection — Python equivalent of lib/interview-models.ts
"""

import os

_DEFAULT_MODELS: dict[str, str] = {
    "start":   "nvidia/nemotron-mini-4b-instruct",
    "respond": "mistralai/mistral-small-4-119b-2603",
    "end":     "meta/llama-3.3-70b-instruct",
}

_ENV_KEYS: dict[str, str] = {
    "start":   "INTERVIEW_START_MODEL",
    "respond": "INTERVIEW_RESPOND_MODEL",
    "end":     "INTERVIEW_END_MODEL",
}


def get_interview_model(phase: str) -> str:
    """Return the configured model for the given interview phase."""
    env_value = os.environ.get(_ENV_KEYS.get(phase, ""), "").strip()
    return env_value or _DEFAULT_MODELS.get(phase, "meta/llama-3.3-70b-instruct")
