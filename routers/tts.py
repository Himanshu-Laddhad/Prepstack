"""
Text-to-speech route — /api/tts
"""

import os

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from auth import MockUser, get_current_user
from lib.constants import ELEVENLABS_VOICES

router = APIRouter(prefix="/api/tts", tags=["tts"])


class TTSRequest(BaseModel):
    text: str = Field(max_length=5000)
    voice: str = Field(default="alex")


@router.post("")
async def text_to_speech(
    body: TTSRequest,
    user: MockUser = Depends(get_current_user),
):
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="TTS not configured")

    voice_key = body.voice if body.voice in ELEVENLABS_VOICES else "alex"
    voice_id = ELEVENLABS_VOICES[voice_key]

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream",
            headers={
                "xi-api-key": api_key,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg",
            },
            json={
                "text": body.text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
            },
        )

    if not response.is_success:
        raise HTTPException(status_code=500, detail="TTS generation failed")

    return Response(
        content=response.content,
        media_type="audio/mpeg",
        headers={"Cache-Control": "no-cache"},
    )
