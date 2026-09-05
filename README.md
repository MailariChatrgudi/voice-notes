# Voice Notes Action Desk

Turn a voice note or meeting transcript into a concise summary, action items, decisions, and unanswered questions.

The project includes:

- A FastAPI backend with text and audio endpoints.
- A browser UI for microphone recording, audio upload, and transcript input.
- Local speech-to-text with `faster-whisper`.
- Structured action-item extraction through OpenRouter.
- A command-line workflow for scripts and batch processing.

## Requirements

- Python 3.10 or newer.
- An OpenRouter API key for AI responses.
- Internet access on the first Whisper run so the selected model can download.
- A working microphone for live recording.

## Installation

From the project directory, create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the API and test dependencies:

```powershell
pip install -r requirements.txt
```

Install audio support when using microphone recording or audio uploads:

```powershell
pip install -r requirements-audio.txt
```

Create the local environment file:

```powershell
Copy-Item .env.example .env
```

Open `.env` and set your OpenRouter key:

```env
OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_MODEL=openrouter/free
```

`openrouter/free` lets OpenRouter choose an available free model. You can replace it with another model supported by your OpenRouter account.

## Browser UI

Start the development server:

```powershell
python -m uvicorn voice_notes_action_items.api:app --reload
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser. You can:

1. Record a voice note with the browser microphone.
2. Upload an audio file.
3. Paste a transcript.
4. Review the generated summary, action items, decisions, and open questions.

The automatic API documentation is available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

## Command Line

Process the included sample transcript:

```powershell
python main.py --text samples\meeting_note.txt
```

Process an audio file:

```powershell
python main.py --audio "C:\path\to\voice-note.mp3" --audio-model tiny
```

Record from the local microphone:

```powershell
python main.py --live --record-seconds 20 --audio-model tiny
```

The recording is saved in `outputs/`. To save the structured result or transcript:

```powershell
python main.py --text samples\meeting_note.txt --output outputs\actions.json
python main.py --audio "C:\path\to\voice-note.mp3" --save-transcript outputs\transcript.txt
```

## API Examples

Create action items from text:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/action-items/text" `
  -H "Content-Type: application/json" `
  -d "{\"transcript\":\"Priya will finish the landing page copy by Friday.\"}"
```

Create action items from audio:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/action-items/audio" `
  -F "file=@C:\path\to\voice-note.mp3" `
  -F "audio_model=tiny" `
  -F "language=en"
```

## Configuration

| Variable | Purpose | Default |
| --- | --- | --- |
| `OPENROUTER_API_KEY` | Required API key | None |
| `OPENROUTER_MODEL` | OpenRouter model name | `openrouter/free` |
| `OPENROUTER_BASE_URL` | OpenRouter-compatible API URL | `https://openrouter.ai/api/v1` |
| `OPENROUTER_HTTP_REFERER` | Optional OpenRouter attribution URL | `http://localhost` |
| `OPENROUTER_APP_TITLE` | Optional OpenRouter app title | `AI Voice Notes Action Items` |
| `WHISPER_MODEL` | Default local transcription model | `base` |
| `VOICE_LANGUAGE` | Optional transcription language | `en` |

## Testing

Run the test suite with the virtual environment active:

```powershell
python -m pytest -q
```

The tests mock Whisper and OpenRouter, so they do not need a microphone, downloaded model, or API key.

## Troubleshooting

### Whisper cannot download a model

Connect to the internet and retry with the smaller model:

```powershell
python main.py --live --record-seconds 20 --audio-model tiny
```

The audio recording is retained in `outputs/`, so it can be transcribed later with `--audio`.

### Microphone recording fails

Check Windows microphone permissions, confirm a microphone is connected, and verify that audio dependencies were installed with `requirements-audio.txt`.

### OpenRouter requests fail

Check that `.env` exists, `OPENROUTER_API_KEY` is valid, the selected model is available, and the machine can reach `openrouter.ai`.

## Privacy

Audio is recorded and transcribed locally. The resulting transcript text is sent to the configured OpenRouter model for action-item extraction.
