"""Local text-to-speech — the delivery layer of the engine.

Wraps `kokoro-onnx` (open-source, Apache-2.0) behind a small, owned
`Voice` interface — same pattern as `inference.py`. Model weights are
fetched directly from the kokoro-onnx project's GitHub releases and
cached locally; there's no third-party orchestrator between us and the
voice.

In the v0 product split (CLAUDE.md), text is the thinking layer; voice
is what the user listens to with their eyes closed. This module is the
voice layer.
"""

from __future__ import annotations

import io
import logging
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import soundfile as sf
from kokoro_onnx import Kokoro

from imagination_engine.config import config

log = logging.getLogger(__name__)

CACHE_DIR = Path.home() / ".cache" / "imagination_engine" / "kokoro"


def _download(url: str, dest: Path) -> None:
    """Download `url` to `dest` if not already present. Shows progress.

    Progress is throttled to ~one update per 5% so a TTY shows movement
    without flooding captured output.
    """
    if dest.exists():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    log.info("Downloading %s -> %s", url, dest)

    last_bucket = -1

    def _progress(block_num: int, block_size: int, total_size: int) -> None:
        nonlocal last_bucket
        if total_size <= 0:
            return
        done = block_num * block_size
        bucket = int(20 * done / total_size)  # 0..20 → every 5%
        if bucket == last_bucket:
            return
        last_bucket = bucket
        pct = 5 * bucket
        mb_done = done / (1024 * 1024)
        mb_total = total_size / (1024 * 1024)
        print(f"  {pct:3d}%  ({mb_done:6.1f} / {mb_total:6.1f} MB)", flush=True)

    urllib.request.urlretrieve(url, tmp, reporthook=_progress)
    tmp.rename(dest)


def _ensure_weights() -> tuple[Path, Path]:
    """Cache Kokoro model + voices files locally, downloading if needed."""
    model_path = CACHE_DIR / Path(config.tts_model_url).name
    voices_path = CACHE_DIR / Path(config.tts_voices_url).name
    _download(config.tts_model_url, model_path)
    _download(config.tts_voices_url, voices_path)
    return model_path, voices_path


@dataclass
class Voice:
    """A loaded local TTS engine, ready to render text into audio."""

    engine: Kokoro
    voice_name: str
    speed: float

    @classmethod
    def load(
        cls,
        *,
        voice_name: str | None = None,
        speed: float | None = None,
    ) -> "Voice":
        model_path, voices_path = _ensure_weights()
        engine = Kokoro(str(model_path), str(voices_path))
        return cls(
            engine=engine,
            voice_name=voice_name or config.tts_voice,
            speed=speed if speed is not None else config.tts_speed,
        )

    def speak(self, text: str, *, speed: float | None = None) -> bytes:
        """Render `text` to a WAV audio bytestring.

        Returns a complete WAV file as bytes — the FastAPI endpoint
        streams these straight to the browser's <audio> element.
        """
        audio, sample_rate = self.engine.create(
            text,
            voice=self.voice_name,
            speed=speed if speed is not None else self.speed,
            lang="en-us",
        )
        buf = io.BytesIO()
        sf.write(buf, audio, sample_rate, format="WAV")
        return buf.getvalue()

    def list_voices(self) -> list[str]:
        return self.engine.get_voices()

    def render_session(
        self,
        script: str,
        *,
        pause_between_paragraphs: float = 2.0,
        speed: float | None = None,
    ) -> bytes:
        """Render a full session script to a single WAV file.

        The script is split at blank-line paragraph breaks. Each paragraph
        is rendered separately, and a real silence (default 2.0 s) is
        inserted between them. That silence is what gives the spoken
        session its breathing room — TTS engines compress pauses inside a
        single render, so we get the spacing by rendering in chunks and
        concatenating.

        Returns a complete WAV file as bytes.
        """
        import numpy as np  # local: tts module already imports soundfile

        paragraphs = [p.strip() for p in script.split("\n\n") if p.strip()]
        if not paragraphs:
            raise ValueError("empty script")

        effective_speed = speed if speed is not None else self.speed

        rendered: list[np.ndarray] = []
        sample_rate = 24000  # Kokoro outputs 24 kHz
        for i, paragraph in enumerate(paragraphs):
            audio, sr = self.engine.create(
                paragraph,
                voice=self.voice_name,
                speed=effective_speed,
                lang="en-us",
            )
            sample_rate = sr
            rendered.append(np.asarray(audio, dtype=np.float32))
            if i < len(paragraphs) - 1:
                silence = np.zeros(
                    int(pause_between_paragraphs * sample_rate),
                    dtype=np.float32,
                )
                rendered.append(silence)

        full = np.concatenate(rendered)
        buf = io.BytesIO()
        sf.write(buf, full, sample_rate, format="WAV")
        return buf.getvalue()
