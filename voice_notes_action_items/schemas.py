from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str


class TranscriptRequest(BaseModel):
    transcript: str = Field(..., min_length=1)


class ActionItem(BaseModel):
    task: str | None = None
    owner: str | None = None
    due_date: str | None = None
    priority: Literal["low", "medium", "high"] = "medium"
    evidence: str | None = None


class ActionItemsResponse(BaseModel):
    summary: str = ""
    action_items: list[ActionItem] = Field(default_factory=list)
    decisions: list[str] = Field(default_factory=list)
    unanswered_questions: list[str] = Field(default_factory=list)
    transcript: str | None = None
