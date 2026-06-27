from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.services.speech_transcription_service import SpeechTranscriptionService

router = APIRouter()
service = SpeechTranscriptionService()


@router.post("/transcribe")
async def transcribe_speech(
    audio: UploadFile = File(...),
    lang: str = Form(default="th-TH"),
) -> dict[str, str]:
    try:
        audio_bytes = await audio.read()
        text = await service.transcribe(
            audio_bytes=audio_bytes,
            filename=audio.filename or "speech.webm",
            content_type=audio.content_type,
            lang=lang,
        )
        return {"text": text}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Speech transcription failed. Please try again.",
        ) from exc