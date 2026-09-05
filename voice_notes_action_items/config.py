from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class AppConfig:
    api_key: str
    model: str
    base_url: str
    http_referer: str
    app_title: str

    @classmethod
    def from_env(cls) -> "AppConfig":
        load_dotenv()

        api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError(
                "Missing OPENROUTER_API_KEY. Add it to .env or your environment."
            )

        return cls(
            api_key=api_key,
            model=os.getenv("OPENROUTER_MODEL", "openrouter/free").strip(),
            base_url=os.getenv(
                "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
            ).strip(),
            http_referer=os.getenv(
                "OPENROUTER_HTTP_REFERER", "http://localhost"
            ).strip(),
            app_title=os.getenv(
                "OPENROUTER_APP_TITLE", "AI Voice Notes Action Items"
            ).strip(),
        )
