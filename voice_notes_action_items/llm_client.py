from __future__ import annotations

from typing import Any

import requests

from voice_notes_action_items.config import AppConfig


class OpenRouterClient:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def chat(self, messages: list[dict[str, str]], json_mode: bool = True) -> str:
        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 1200,
        }

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        try:
            response = requests.post(
                f"{self.config.base_url.rstrip('/')}/chat/completions",
                headers=self._headers(),
                json=payload,
                timeout=90,
            )
        except requests.RequestException as error:
            raise RuntimeError(
                "Could not connect to OpenRouter. Check your internet connection, "
                "VPN/proxy/firewall settings, and whether network access is allowed "
                f"for this terminal. Original error: {str(error)[:500]}"
            ) from error

        if self._should_retry_without_json_mode(response, json_mode):
            return self.chat(messages, json_mode=False)

        if response.status_code >= 400:
            raise RuntimeError(
                f"OpenRouter request failed with {response.status_code}: "
                f"{response.text[:500]}"
            )

        try:
            data = response.json()
        except ValueError as error:
            raise RuntimeError(
                f"OpenRouter returned a non-JSON response: {response.text[:500]}"
            ) from error
        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError("OpenRouter returned no choices.")

        content = choices[0].get("message", {}).get("content", "")
        if not content:
            raise RuntimeError("OpenRouter returned an empty message.")

        return content

    @staticmethod
    def _should_retry_without_json_mode(
        response: requests.Response, json_mode: bool
    ) -> bool:
        if not json_mode or response.status_code not in {400, 422}:
            return False

        error_text = response.text.lower()
        return "response_format" in error_text or "json" in error_text

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.config.http_referer,
            "X-OpenRouter-Title": self.config.app_title,
        }
