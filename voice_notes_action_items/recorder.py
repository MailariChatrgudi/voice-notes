from __future__ import annotations

import queue
import wave
from datetime import datetime
from pathlib import Path


def record_live_audio(
    output_path: Path | None = None,
    seconds: float | None = None,
    sample_rate: int = 16000,
    channels: int = 1,
) -> Path:
    try:
        import sounddevice as sd
    except ImportError as error:
        raise RuntimeError(
            "Live microphone recording needs sounddevice. "
            "Install it with: pip install -r requirements-audio.txt"
        ) from error

    if seconds is not None and seconds <= 0:
        raise ValueError("--record-seconds must be greater than 0.")

    output_path = output_path or default_recording_path()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    audio_queue: queue.Queue[bytes] = queue.Queue()

    def callback(indata, _frames, _time, status) -> None:
        if status:
            print(f"Audio warning: {status}")
        audio_queue.put(bytes(indata))

    print("Microphone recording uses your computer's mic permission.")
    input("Press Enter to start recording...")

    try:
        with wave.open(str(output_path), "wb") as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)

            with sd.RawInputStream(
                samplerate=sample_rate,
                channels=channels,
                dtype="int16",
                callback=callback,
            ):
                if seconds:
                    print(f"Recording for {seconds:g} seconds...")
                    sd.sleep(int(seconds * 1000))
                else:
                    print("Recording... press Enter to stop.")
                    input()

                while not audio_queue.empty():
                    wav_file.writeframes(audio_queue.get())
    except KeyboardInterrupt as error:
        raise RuntimeError("Recording cancelled.") from error
    except Exception as error:
        raise RuntimeError(
            "Could not record from the microphone. Check Windows microphone "
            "privacy settings and make sure a microphone is connected."
        ) from error

    print(f"Saved live recording to {output_path}")
    return output_path


def default_recording_path() -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path("outputs") / f"live_voice_note_{timestamp}.wav"
