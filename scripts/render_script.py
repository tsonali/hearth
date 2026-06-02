"""Render an existing session script.txt to audio in a chosen voice.

Single-model render (no generation) — for HEARING a session without the
Qwen+TTS double-load. F5 renders at ~1/4-1/8x real-time, so a full session
takes tens of minutes. Run in the background.

    .venv/bin/python scripts/render_script.py <script.txt> [f5|her|him|kokoro]
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from imagination_engine.tts import make_voice  # noqa: E402


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: render_script.py <script.txt> [backend]", file=sys.stderr)
        return 1
    script_path = Path(sys.argv[1])
    backend = sys.argv[2] if len(sys.argv) > 2 else "f5"
    if not script_path.is_file():
        print(f"no such script: {script_path}", file=sys.stderr)
        return 1

    text = script_path.read_text(encoding="utf-8")
    words = len(text.split())
    out = script_path.parent / f"session-{backend}.wav"

    print(f"script: {script_path} ({words} words)", flush=True)
    print(f"loading '{backend}' voice ...", flush=True)
    voice = make_voice(backend)
    print("rendering (F5 is slow — ~1/4-1/8x real-time; be patient) ...", flush=True)
    t0 = time.time()
    wav_bytes = voice.render_session(text)
    out.write_bytes(wav_bytes)
    secs = time.time() - t0
    print(f"DONE in {secs:.0f}s -> {out} ({len(wav_bytes)/1024:.0f} KB)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
