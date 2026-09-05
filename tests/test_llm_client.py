from __future__ import annotations

import requests

from voice_notes_action_items.config import AppConfig
from voice_notes_action_items.llm_client import OpenRouterClient


def make_client() -> OpenRouterClient:
    config = AppConfig(
        api_key="test-key",
        model="openrouter/free",
        base_url="https://openrouter.ai/api/v1",
        http_referer="http://localhost",
        app_title="tests",
    )
    return OpenRouterClient(config)


def test_chat_returns_content(monkeypatch) -> None:
    class FakeResponse:
        status_code = 200
        text = ""

        def json(self) -> dict:
            return {"choices": [{"message": {"content": "hello"}}]}

    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: FakeResponse())

    result = make_client().chat([{"role": "user", "content": "hi"}])

    assert result == "hello"


def test_chat_raises_friendly_network_error(monkeypatch) -> None:
    def fail_post(*args, **kwargs):
        raise requests.ConnectionError("network blocked")

    monkeypatch.setattr(requests, "post", fail_post)

    try:
        make_client().chat([{"role": "user", "content": "hi"}])
    except RuntimeError as error:
        assert "Could not connect to OpenRouter" in str(error)
        assert "network blocked" in str(error)
    else:
        raise AssertionError("Expected RuntimeError")
