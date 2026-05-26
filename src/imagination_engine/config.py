"""Single source of truth for paths, model identifier, and server defaults."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Config:
    # Llama 3.1 8B Instruct, 4-bit MLX quantization, from Hugging Face.
    # Pulled directly via mlx-lm's HF integration; no third-party registry.
    model_id: str = "mlx-community/Meta-Llama-3.1-8B-Instruct-4bit"

    # Loopback only — the product is local-first; the server must not be
    # reachable from outside this machine.
    host: str = "127.0.0.1"
    port: int = 8765

    # Generation defaults. Per-protocol overrides come later.
    max_tokens: int = 512
    temperature: float = 0.7

    # Local TTS — Kokoro-82M ONNX (Apache-2.0). Canonical weight files
    # are hosted on the kokoro-onnx GitHub releases page; we cache them
    # under ~/.cache/imagination_engine/kokoro/. `tts_voice` is the
    # default speaker; `tts_speed` is below 1.0 because guided imagery
    # wants spaciousness, not pace.
    tts_model_url: str = (
        "https://github.com/thewh1teagle/kokoro-onnx/releases/download/"
        "model-files-v1.0/kokoro-v1.0.onnx"
    )
    tts_voices_url: str = (
        "https://github.com/thewh1teagle/kokoro-onnx/releases/download/"
        "model-files-v1.0/voices-v1.0.bin"
    )
    tts_voice: str = "af_heart"
    tts_speed: float = 0.9


config = Config()
