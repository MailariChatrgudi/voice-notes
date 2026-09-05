from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from voice_notes_action_items import api


client = TestClient(api.app)


def fake_action_items_result(transcript: str) -> dict:
    return {
        "summary": f"Summary for: {transcript[:20]}",
        "action_items": [
            {
                "task": "Send launch email draft",
                "owner": "Arjun",
                "due_date": None,
                "priority": "medium",
                "evidence": "share it with marketing tomorrow",
            }
        ],
        "decisions": ["Launch beta after QA sign-off."],
        "unanswered_questions": ["Is an onboarding video needed?"],
    }


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "voice-notes-action-items",
    }


def test_frontend_homepage() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "Action Desk" in response.text


def test_action_items_from_text(monkeypatch) -> None:
    monkeypatch.setattr(api, "build_client", lambda: object())
    monkeypatch.setattr(
        api,
        "extract_action_items",
        lambda transcript, _client: fake_action_items_result(transcript),
    )

    response = client.post(
        "/action-items/text",
        json={"transcript": "Arjun will send the launch email draft."},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["summary"].startswith("Summary for")
    assert data["action_items"][0]["owner"] == "Arjun"
    assert data["transcript"] is None


def test_action_items_from_text_rejects_blank_transcript() -> None:
    response = client.post("/action-items/text", json={"transcript": "   "})

    assert response.status_code == 400
    assert response.json()["detail"] == "Transcript cannot be empty."


def test_action_items_from_audio(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(api, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(api, "build_client", lambda: object())
    monkeypatch.setattr(
        api,
        "transcribe_audio",
        lambda audio_path, model_size=None, language=None: (
            f"Transcript from {Path(audio_path).suffix}"
        ),
    )
    monkeypatch.setattr(
        api,
        "extract_action_items",
        lambda transcript, _client: fake_action_items_result(transcript),
    )

    response = client.post(
        "/action-items/audio",
        files={"file": ("note.wav", b"fake audio", "audio/wav")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["transcript"] == "Transcript from .wav"
    assert data["action_items"][0]["task"] == "Send launch email draft"
    assert list(tmp_path.iterdir())
