from __future__ import annotations

import argparse
import json
from pathlib import Path

from voice_notes_action_items.action_items import extract_action_items
from voice_notes_action_items.config import AppConfig
from voice_notes_action_items.llm_client import OpenRouterClient
from voice_notes_action_items.recorder import record_live_audio
from voice_notes_action_items.transcriber import transcribe_audio


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Turn voice notes or transcripts into action items with OpenRouter."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--audio", type=Path, help="Path to an audio voice note.")
    source.add_argument("--text", type=Path, help="Path to a transcript text file.")
    source.add_argument(
        "--live",
        action="store_true",
        help="Record a live voice note from your microphone.",
    )

    parser.add_argument("--output", type=Path, help="Optional JSON output file.")
    parser.add_argument(
        "--save-transcript",
        type=Path,
        help="Optional text file to save the transcript when using --audio or --live.",
    )
    parser.add_argument(
        "--audio-model",
        default=None,
        help="Whisper model size for audio transcription, such as tiny, base, or small.",
    )
    parser.add_argument(
        "--language",
        default=None,
        help="Audio language code for Whisper, such as en or hi.",
    )
    parser.add_argument(
        "--record-seconds",
        type=float,
        default=None,
        help="Optional live recording length. If omitted, press Enter to stop.",
    )
    parser.add_argument(
        "--record-output",
        type=Path,
        default=None,
        help="Optional WAV file path for live microphone recording.",
    )
    return parser.parse_args()


def read_transcript(args: argparse.Namespace) -> str:
    if args.text:
        if not args.text.exists():
            raise FileNotFoundError(f"Text file not found: {args.text}")
        return args.text.read_text(encoding="utf-8").strip()

    audio_path = args.audio
    if args.live:
        audio_path = record_live_audio(
            output_path=args.record_output,
            seconds=args.record_seconds,
        )

    transcript = transcribe_audio(
        audio_path,
        model_size=args.audio_model,
        language=args.language,
    )

    if args.save_transcript:
        args.save_transcript.parent.mkdir(parents=True, exist_ok=True)
        args.save_transcript.write_text(transcript, encoding="utf-8")

    return transcript.strip()


def print_result(result: dict) -> None:
    print("\nSummary")
    print(f"- {result.get('summary', 'No summary returned.')}")

    print("\nAction Items")
    action_items = result.get("action_items", [])
    if not action_items:
        print("- No action items found.")
    for index, item in enumerate(action_items, start=1):
        owner = item.get("owner") or "Unassigned"
        due_date = item.get("due_date") or "No due date"
        priority = item.get("priority") or "medium"
        task = item.get("task") or "Untitled task"
        print(f"{index}. [{priority}] {task} | Owner: {owner} | Due: {due_date}")

    decisions = result.get("decisions", [])
    if decisions:
        print("\nDecisions")
        for decision in decisions:
            print(f"- {decision}")

    questions = result.get("unanswered_questions", [])
    if questions:
        print("\nOpen Questions")
        for question in questions:
            print(f"- {question}")


def main() -> None:
    args = parse_args()
    transcript = read_transcript(args)
    if not transcript:
        raise SystemExit("The transcript is empty. Please provide a valid note.")

    config = AppConfig.from_env()
    client = OpenRouterClient(config)
    result = extract_action_items(transcript, client)

    print_result(result)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"\nSaved JSON to {args.output}")


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, RuntimeError, ValueError) as error:
        raise SystemExit(f"\nError: {error}") from error
