"""Single source of truth for paths, model identifier, and server defaults."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RECORDINGS_DIR = DATA_DIR / "recordings"
RECORDING_SCRIPT = DATA_DIR / "recording-script.json"
SPEAKERS_REGISTRY = DATA_DIR / "speakers.json"

# Curated system voices — the two first-class non-user options.
# Each is a short reference clip we feed to Chatterbox for zero-shot cloning.
# See data/system_voices/README.md for sourcing notes.
SYSTEM_VOICES_DIR = DATA_DIR / "system_voices"

# Rendered session audio — WAV + MP3 written here after generation.
# WAV is the source-of-truth (lossless, plays inline in the browser);
# MP3 is the smaller download/share artifact (AirDrop, save to phone).
# Gitignored — these are derived artifacts, regenerable from the script.
SESSIONS_DIR = DATA_DIR / "sessions"

# Local memory store — SQLite, on-disk, gitignored, NEVER transmitted.
# Holds one row per completed session. Used by the intake to weave in
# light references to recent imaginings. The user does NOT see a
# scrollable history; the memory is the engine's, not the user's.
MEMORY_DB = DATA_DIR / "memory.sqlite"


@dataclass(frozen=True)
class Config:
    # Qwen 2.5 14B Instruct, 4-bit MLX quantization, from Hugging Face.
    # Chosen over Llama 3.1 8B / Mistral NeMo 12B after the 2026-05-29 bake-off:
    # Qwen was the ONLY candidate with zero JSON-parse failures (0/5 vs 3/5),
    # and its quality was competitive once the weak local judge's mis-score was
    # discounted by direct read. Its only cost is generation speed (~17 min/script),
    # acceptable for batch/overnight runs (esp. on the dedicated grind box).
    # Pulled directly via mlx-lm's HF integration; no third-party registry.
    # See docs/decisions-log.md (2026-05-29 — model bake-off).
    model_id: str = "mlx-community/Qwen2.5-14B-Instruct-4bit"
    # Our fine-tuned LoRA adapter. If this dir has *.safetensors, the product runs on
    # OUR specialist instead of stock Qwen (Engine.load falls back to base if absent).
    # Drop the trained adapter here to ship our model: data/model/adapters/
    adapter_path: str = str(DATA_DIR / "model" / "adapters")

    # Speculative decoding — MEASURED A SLOWDOWN HERE, default off. The
    # 2026-06-10 benchmark (Qwen2.5-0.5B draft, order-controlled): 0.60x vs
    # baseline. Cause: our creative sampling (temp 0.85 + top_p + repetition
    # penalty) diverges from the draft's proposals, so most drafts are rejected
    # and verification is wasted work. Spec decoding wins at low temperature;
    # sessions run hot by design. Plumbing kept for future low-temp use.
    # See docs/decisions-log.md.
    draft_model_id: str = ""
    num_draft_tokens: int = 4

    # Loopback only — the product is local-first; the server must not be
    # reachable from outside this machine.
    host: str = "127.0.0.1"
    port: int = 8765

    # Generation defaults. Per-protocol overrides come later.
    max_tokens: int = 512
    temperature: float = 0.8
    # Nucleus sampling — restrict each token choice to the top `top_p` of
    # probability mass. Diversifies output and avoids tail-token weirdness.
    top_p: float = 0.92
    # Penalty for repeating tokens within `repetition_context_size`.
    # 1.0 = no penalty, 1.1-1.2 = gentle, 1.3+ = strong. Prevents the
    # "justice-broker justice-broker…" degenerate-loop failure mode.
    repetition_penalty: float = 1.15
    repetition_context_size: int = 64

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

    # Production voice: F5-TTS fine-tuned on the speaker's own recordings.
    # Used when the user picks "your voice" at intake. Checkpoint lives in
    # the f5_tts ckpts directory; reference clip lives in data/dataset/.
    #
    # ⚠️ LICENSING (verified 2026-05-29): F5-TTS *code* is MIT but the pre-trained
    # *weights* are CC-BY-NC (Emilia training data) — NON-COMMERCIAL, even after
    # fine-tuning. Fine for dev/personal use; CANNOT ship in a distributed product.
    # Before distribution, swap the user-voice-cloning path to a commercial-clean
    # base (Kokoro=Apache-2.0, Chatterbox=MIT, or NeuTTS Air). See decisions-log
    # 2026-05-29 "Licensing landmines."
    f5_speaker: str = "sonali"
    f5_checkpoint: str = "model_3000.pt"
    f5_ref_id: str = "g021"
    f5_ref_text: str = (
        "The dog dropped the rope at her feet and looked up, plainly waiting."
    )
    f5_speed: float = 1.0
    f5_cfg_strength: float = 2.0
    f5_nfe_step: int = 32

    # Chatterbox (Resemble AI, MIT) — the two curated system voices.
    # Zero-shot cloned from a ~15s reference clip per speaker. Tuned for
    # the "relaxed, intimate, audiobook-narrator" feel that suits a 12-min
    # eyes-closed session. See tts.py:ChatterboxVoice for the per-knob
    # rationale; these defaults are the calm end of the dial.
    chatterbox_exaggeration: float = 0.35   # 0.0-1.0; lower = calmer, less animated
    chatterbox_cfg_weight: float = 0.5      # how closely it tracks the reference
    chatterbox_temperature: float = 0.7     # sampling stochasticity; lower = steadier
    # 40-sec per-render cap → ~75 words max. Stay well under for safety.
    chatterbox_max_words_per_chunk: int = 55
    # Crossfade between sub-chunks of a single paragraph, in milliseconds.
    chatterbox_crossfade_ms: int = 40


config = Config()
