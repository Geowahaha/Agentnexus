from __future__ import annotations

import httpx

from app.core.config import settings

WHISPER_MAX_BYTES = 10 * 1024 * 1024
WHISPER_MODEL = "whisper-1"


def normalize_audio_content_type(filename: str, content_type: str | None) -> str:
    lowered = (filename or "").lower()
    if lowered.endswith((".m4a", ".mp4", ".caf")):
        return "audio/mp4"
    if lowered.endswith(".webm"):
        return "audio/webm"
    if lowered.endswith(".ogg"):
        return "audio/ogg"
    if lowered.endswith(".wav"):
        return "audio/wav"
    if lowered.endswith((".mp3", ".mpeg", ".mpga")):
        return "audio/mpeg"
    if content_type and content_type != "application/octet-stream":
        return content_type.split(";", 1)[0].strip()
    return "application/octet-stream"


def normalize_whisper_language(lang: str | None) -> str | None:
    if not lang:
        return None
    normalized = lang.strip().lower()
    if normalized.startswith("th"):
        return "th"
    if normalized.startswith("en"):
        return "en"
    if len(normalized) == 2:
        return normalized
    return None


class SpeechTranscriptionService:
    async def transcribe(
        self,
        *,
        audio_bytes: bytes,
        filename: str,
        content_type: str | None,
        lang: str | None,
    ) -> str:
        if not settings.openai_api_key:
            raise RuntimeError(
                "Speech transcription is not configured. Set OPENAI_API_KEY on the API server."
            )
        if not audio_bytes:
            raise ValueError("Audio file is empty.")
        if len(audio_bytes) > WHISPER_MAX_BYTES:
            raise ValueError("Audio file is too large. Maximum size is 10 MB.")

        whisper_lang = normalize_whisper_language(lang)
        data: dict[str, str] = {"model": WHISPER_MODEL}
        if whisper_lang:
            data["language"] = whisper_lang

        resolved_type = normalize_audio_content_type(filename, content_type)
        files = {
            "file": (
                filename or "speech.webm",
                audio_bytes,
                resolved_type,
            )
        }

        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                data=data,
                files=files,
            )

        if response.status_code >= 400:
            detail = response.text.strip() or response.reason_phrase
            raise RuntimeError(f"Whisper transcription failed ({response.status_code}): {detail}")

        payload = response.json()
        text = str(payload.get("text", "")).strip()
        if not text:
            raise ValueError("No speech detected in the recording.")
        return text