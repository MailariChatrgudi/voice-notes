from __future__ import annotations

import os
from pathlib import Path


def transcribe_audio(
    audio_path: Path,
    model_size: str | None = None,
    language: str | None = None,
) -> str:
    if not audio_path.exists():
        raise FileNotFoundError(
            f"Audio file not found: {audio_path}. "
            "Replace the example path with a real audio file path, for example: "
            'python main.py --audio "C:\\Users\\HP\\Downloads\\voice-note.mp3"'
        )

    try:
        from faster_whisper import WhisperModel
    except ImportError as error:
        raise RuntimeError(
            "Audio transcription needs faster-whisper. "
            "Install it with: pip install -r requirements-audio.txt"
        ) from error

    selected_model = model_size or os.getenv("WHISPER_MODEL", "base")
    selected_language = language or os.getenv("VOICE_LANGUAGE") or None

    print(f"Transcribing audio with Whisper model: {selected_model}")
    print("First run may download this model from Hugging Face.")

    try:
        model = WhisperModel(selected_model, device="cpu", compute_type="int8")
        segments, _info = model.transcribe(
            str(audio_path),
            language=selected_language,
            vad_filter=True,
        )
    except Exception as error:
        raise RuntimeError(
            build_transcription_error_message(selected_model, error)
        ) from error

    transcript_parts = [segment.text.strip() for segment in segments]
    return " ".join(part for part in transcript_parts if part)


def build_transcription_error_message(model_name: str, error: Exception) -> str:
    error_text = str(error)
    message = (
        f"Could not load or run the Whisper model '{model_name}'. "
        "Your microphone recording was saved, but transcription could not start."
    )

    if "getaddrinfo failed" in error_text or "Hub" in error_text:
        message += (
            "\n\nThis usually means the model is not downloaded yet and Python "
            "could not connect to Hugging Face.\n"
            "Fix options:\n"
            "1. Connect to the internet, then run the same command again.\n"
            "2. Try a smaller first-download model: python main.py --live "
            "--record-seconds 20 --audio-model tiny\n"
            "3. Reuse your saved recording after the download works: python main.py "
            "--audio outputs\\live_voice_note_YYYYMMDD_HHMMSS.wav"
        )
    else:
        message += (
            "\n\nCheck that the audio file is valid and the audio dependencies are "
            "installed with: pip install -r requirements-audio.txt"
        )

    message += f"\n\nOriginal error: {error_text[:500]}"
    return message
