from __future__ import annotations

import json
from ast import literal_eval
from datetime import date
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from voice_notes_action_items.llm_client import OpenRouterClient


SYSTEM_PROMPT = """
You extract useful work items from messy voice-note transcripts.
Return valid JSON only. Do not include markdown, comments, or trailing commas.
""".strip()


def build_prompt(transcript: str) -> str:
    today = date.today().isoformat()
    return f"""
Today is {today}.

Read this transcript and create action items.

Return JSON with exactly these keys:
- summary: one short paragraph
- action_items: list of objects with task, owner, due_date, priority, and evidence
- decisions: list of strings
- unanswered_questions: list of strings

Use this exact JSON shape:
{{
  "summary": "",
  "action_items": [
    {{
      "task": "",
      "owner": null,
      "due_date": null,
      "priority": "medium",
      "evidence": ""
    }}
  ],
  "decisions": [],
  "unanswered_questions": []
}}

Rules:
- Use null when owner or due_date is not mentioned.
- due_date should be YYYY-MM-DD when the transcript gives enough information.
- priority must be low, medium, or high.
- evidence should be a short phrase from the transcript.
- Do not invent tasks that are not supported by the transcript.

Transcript:
{transcript}
""".strip()


def extract_action_items(transcript: str, client: "OpenRouterClient") -> dict[str, Any]:
    content = client.chat(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_prompt(transcript)},
        ]
    )

    try:
        result = parse_json_object(content)
    except ValueError:
        repaired_content = repair_json_response(content, client)
        result = parse_json_object(repaired_content)

    return normalize_result(result)


def repair_json_response(content: str, client: "OpenRouterClient") -> str:
    repair_prompt = f"""
Convert the text below into valid JSON.

Return only a JSON object with these keys:
- summary
- action_items
- decisions
- unanswered_questions

Rules:
- Use double quotes for all JSON keys and strings.
- Use null, true, and false where needed.
- Remove markdown fences and comments.
- Do not add new facts.

Text to convert:
{content[:6000]}
""".strip()

    return client.chat(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": repair_prompt},
        ]
    )


def parse_json_object(content: str) -> dict[str, Any]:
    cleaned = strip_markdown_fence(content)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    candidates = [cleaned]

    if start != -1 and end != -1 and end > start:
        candidates.append(cleaned[start : end + 1])

    for candidate in candidates:
        parsed = parse_json_candidate(candidate)
        if isinstance(parsed, dict):
            return parsed

    raise ValueError(f"Model did not return a valid JSON object: {content[:300]}")


def parse_json_candidate(candidate: str) -> Any:
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    try:
        return literal_eval(candidate)
    except (SyntaxError, ValueError):
        return None


def normalize_result(result: dict[str, Any]) -> dict[str, Any]:
    action_items = result.get("action_items") or []
    decisions = result.get("decisions") or []
    unanswered_questions = result.get("unanswered_questions") or []

    if not isinstance(action_items, list):
        action_items = []
    if not isinstance(decisions, list):
        decisions = []
    if not isinstance(unanswered_questions, list):
        unanswered_questions = []

    return {
        "summary": str(result.get("summary", "")).strip(),
        "action_items": [
            normalize_action_item(item)
            for item in action_items
            if isinstance(item, dict)
        ],
        "decisions": [
            str(item).strip()
            for item in decisions
            if str(item).strip()
        ],
        "unanswered_questions": [
            str(item).strip()
            for item in unanswered_questions
            if str(item).strip()
        ],
    }


def normalize_action_item(item: dict[str, Any]) -> dict[str, Any]:
    priority = str(item.get("priority", "medium")).lower().strip()
    if priority not in {"low", "medium", "high"}:
        priority = "medium"

    return {
        "task": clean_or_none(item.get("task")),
        "owner": clean_or_none(item.get("owner")),
        "due_date": clean_or_none(item.get("due_date")),
        "priority": priority,
        "evidence": clean_or_none(item.get("evidence")),
    }


def clean_or_none(value: Any) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def strip_markdown_fence(content: str) -> str:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return cleaned
