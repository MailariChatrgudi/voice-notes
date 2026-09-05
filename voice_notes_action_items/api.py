from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles

from voice_notes_action_items.action_items import extract_action_items
from voice_notes_action_items.config import AppConfig
from voice_notes_action_items.llm_client import OpenRouterClient
from voice_notes_action_items.schemas import (
    ActionItemsResponse,
    HealthResponse,
    TranscriptRequest,
)
from voice_notes_action_items.transcriber import transcribe_audio


UPLOAD_DIR = Path("outputs") / "uploads"
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


app = FastAPI(
    title="AI Voice Notes Action Items",
    description="Turn transcripts or uploaded voice notes into action items.",
    version="1.0.0",
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="voice-notes-action-items")


@app.post("/action-items/text", response_model=ActionItemsResponse)
def action_items_from_text(request: TranscriptRequest) -> ActionItemsResponse:
    transcript = request.transcript.strip()
    if not transcript:
        raise HTTPException(status_code=400, detail="Transcript cannot be empty.")

    return build_action_items_response(transcript)


@app.post("/action-items/audio", response_model=ActionItemsResponse)
async def action_items_from_audio(
    file: UploadFile = File(...),
    audio_model: str | None = Form(default=None),
    language: str | None = Form(default=None),
) -> ActionItemsResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Upload must include a file name.")

    audio_path = await save_upload_file(file)

    try:
        transcript = transcribe_audio(
            audio_path,
            model_size=audio_model,
            language=language,
        ).strip()
    except (FileNotFoundError, RuntimeError, ValueError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    if not transcript:
        raise HTTPException(
            status_code=400,
            detail="Audio was transcribed, but no speech text was found.",
        )

    return build_action_items_response(transcript, include_transcript=True)


def build_action_items_response(
    transcript: str,
    include_transcript: bool = False,
) -> ActionItemsResponse:
    try:
        client = build_client()
        result = extract_action_items(transcript, client)
    except (RuntimeError, ValueError) as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

    response_data: dict[str, Any] = dict(result)
    if include_transcript:
        response_data["transcript"] = transcript

    return ActionItemsResponse(**response_data)


def build_client() -> OpenRouterClient:
    return OpenRouterClient(AppConfig.from_env())


async def save_upload_file(file: UploadFile) -> Path:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    suffix = Path(file.filename or "audio.wav").suffix or ".wav"
    output_path = UPLOAD_DIR / f"{uuid.uuid4().hex}{suffix}"

    with output_path.open("wb") as output_file:
        while chunk := await file.read(1024 * 1024):
            output_file.write(chunk)

    await file.close()
    return output_path


app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
