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


config = Config()
