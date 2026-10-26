#!/usr/bin/env python3
"""
voiceclone.py - clone your own voice from a short recording and speak any text with it.

Examples:
  python voiceclone.py --ref my_voice.wav --text "Hello, this is me." --out hello.wav
  python voiceclone.py --ref my_voice.m4a --text-file script.txt
  python voiceclone.py --ref my_voice.wav            # interactive: type text, get audio

Language is auto-detected (Arabic vs English). Override with --lang.
Only clone voices you own or have permission to use.
"""
import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MODEL = "tts_models/multilingual/multi-dataset/xtts_v2"
ARABIC = re.compile(r"[\u0600-\u06FF]")
LANGS = ["en", "ar", "es", "fr", "de", "it", "pt", "pl", "tr", "ru", "nl", "cs", "zh-cn", "ja", "hu", "ko", "hi"]


def detect_lang(text: str) -> str:
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return "en"
    arabic = sum(1 for c in letters if ARABIC.match(c))
    return "ar" if arabic / len(letters) > 0.5 else "en"


def prepare_reference(src: Path, workdir: Path) -> Path:
    """Convert any audio/video file to a clean mono 22.05 kHz WAV (max 30s, leading silence trimmed)."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        if src.suffix.lower() == ".wav":
            print("ffmpeg not found - using the WAV as-is.")
            return src
        sys.exit("ffmpeg is required for non-WAV input. Install it (see README) or provide a .wav file.")
    out = workdir / "reference.wav"
    cmd = [
        ffmpeg, "-y", "-i", str(src),
        "-ac", "1", "-ar", "22050", "-t", "30",
        "-af", "silenceremove=start_periods=1:start_threshold=-45dB",
        str(out),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 or not out.exists():
        sys.exit(f"ffmpeg failed to read the reference file:\n{result.stderr[-500:]}")
    return out


def load_model():
    import torch
    from TTS.api import TTS

    # XTTS is unreliable on Apple's MPS backend, so Macs use CPU (slower but correct).
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading model on {device} (first run downloads ~2 GB)...")
    return TTS(MODEL).to(device), device


def speak(tts, text: str, ref: Path, lang: str, out: Path, speed: float):
    out.parent.mkdir(parents=True, exist_ok=True)
    tts.tts_to_file(
        text=text,
        speaker_wav=str(ref),
        language=lang,
        file_path=str(out),
        speed=speed,
        split_sentences=True,
    )
    print(f"Saved: {out}")


def main():
    p = argparse.ArgumentParser(description="Clone your voice and speak any text with it.")
    p.add_argument("--ref", required=True, type=Path, help="Recording of your voice (wav/mp3/m4a/...). 10-30s of clean speech is ideal.")
    p.add_argument("--text", help="Text to speak.")
    p.add_argument("--text-file", type=Path, help="Read the text from a file (UTF-8).")
    p.add_argument("--lang", choices=LANGS, help="Language code. Default: auto-detect (ar/en).")
    p.add_argument("--out", type=Path, default=Path("output.wav"), help="Output WAV path (single-shot mode).")
    p.add_argument("--speed", type=float, default=1.0, help="Speaking speed, e.g. 0.9 slower, 1.1 faster.")
    args = p.parse_args()

    if not args.ref.exists():
        sys.exit(f"Reference file not found: {args.ref}")

    text = args.text
    if args.text_file:
        text = args.text_file.read_text(encoding="utf-8").strip()

    with tempfile.TemporaryDirectory() as tmp:
        ref = prepare_reference(args.ref, Path(tmp))
        tts, _ = load_model()

        if text:
            speak(tts, text, ref, args.lang or detect_lang(text), args.out, args.speed)
            return

        # Interactive mode: model stays loaded, so each line is fast.
        print("Interactive mode. Type text and press Enter. Empty line or Ctrl+C to quit.")
        n = 1
        while True:
            try:
                line = input("\n> ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not line:
                break
            out = Path(f"output_{n:03d}.wav")
            speak(tts, line, ref, args.lang or detect_lang(line), out, args.speed)
            n += 1


if __name__ == "__main__":
    main()
