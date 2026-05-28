"""Audio helpers — WAV ↔ MP3, session-file persistence.

Sessions are rendered as 24 kHz mono WAV (the inline-playback format the
browser handles natively) and persisted alongside an MP3 encode for the
user to download / AirDrop / save to phone.

MP3 is ~75% smaller than WAV at 96 kbps and good-enough quality for a
narrated session — meditation-app voices ship at 64-96 kbps routinely.
The WAV is the source-of-truth; the MP3 is the share artifact.
"""

from __future__ import annotations

import io
import logging
from pathlib import Path

import soundfile as sf

from imagination_engine.config import SESSIONS_DIR

log = logging.getLogger(__name__)


# 96 kbps mono is the sweet spot for narrated speech — meditation apps
# ship at 64-96; below 64 you start hearing artifacts on sibilants and
# breath. We're not music. Adjust here if you ever want a different point.
DEFAULT_MP3_BITRATE = 96


def wav_to_mp3(wav_bytes: bytes, *, bitrate: int = DEFAULT_MP3_BITRATE) -> bytes:
    """Encode WAV bytes to MP3 bytes.

    Decodes via soundfile, encodes via LAME (lameenc). Mono and stereo both
    handled; the engine generates mono so the stereo path is defensive.
    """
    import lameenc
    import numpy as np

    audio, sr = sf.read(io.BytesIO(wav_bytes), dtype="int16")
    if audio.ndim == 1:
        # Mono — lameenc wants a 2-D shape too, so reshape rather than expand.
        channels = 1
        pcm = audio
    else:
        channels = audio.shape[1]
        pcm = audio

    enc = lameenc.Encoder()
    enc.set_bit_rate(bitrate)
    enc.set_in_sample_rate(sr)
    enc.set_channels(channels)
    enc.set_quality(2)  # 2 = high quality, slower; 7 = fast, lower quality
    mp3_data = enc.encode(pcm.tobytes())
    mp3_data += enc.flush()
    log.info(
        "encoded WAV (%.1fs @ %d Hz) -> MP3 (%d kbps, %.1f KB)",
        len(pcm) / sr / channels if channels else 0,
        sr, bitrate, len(mp3_data) / 1024,
    )
    return mp3_data


def persist_session_audio(session_id: str, wav_bytes: bytes) -> tuple[Path, Path]:
    """Write the session audio to SESSIONS_DIR/{id}.wav and {id}.mp3.

    Returns (wav_path, mp3_path). Caller is responsible for handling errors
    — we let exceptions bubble (disk full, perms, etc.) since they indicate
    something the user should know about.
    """
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    wav_path = SESSIONS_DIR / f"{session_id}.wav"
    mp3_path = SESSIONS_DIR / f"{session_id}.mp3"

    wav_path.write_bytes(wav_bytes)
    mp3_bytes = wav_to_mp3(wav_bytes)
    mp3_path.write_bytes(mp3_bytes)
    log.info("persisted session %s (wav=%.1f KB, mp3=%.1f KB)",
             session_id, len(wav_bytes) / 1024, len(mp3_bytes) / 1024)
    return wav_path, mp3_path


def session_mp3_path(session_id: str) -> Path:
    """Where the rendered session MP3 lives on disk."""
    return SESSIONS_DIR / f"{session_id}.mp3"
