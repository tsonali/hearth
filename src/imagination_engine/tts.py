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
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

import soundfile as sf
from kokoro_onnx import Kokoro

from imagination_engine.config import config


# Same callback shape as generator.ProgressFn — the server passes one in so
# the user-visible "preparing" line gets live updates during a 20-minute F5
# render. See `IntakeSession.progress` for the receiving end.
ProgressFn = Callable[..., None]

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

    @property
    def backend(self) -> str:
        return "kokoro"

    @property
    def display_name(self) -> str:
        return "Quick"

    def render_session(
        self,
        script: str,
        *,
        pause_between_paragraphs: float = 2.0,
        speed: float | None = None,
        on_progress: Optional[ProgressFn] = None,
    ) -> bytes:
        """Render a full session script to a single WAV file.

        The script is split at blank-line paragraph breaks. Each paragraph
        is rendered separately, and a real silence (default 2.0 s) is
        inserted between them. That silence is what gives the spoken
        session its breathing room — TTS engines compress pauses inside a
        single render, so we get the spacing by rendering in chunks and
        concatenating.

        If `on_progress` is supplied, it's invoked before each paragraph
        with stage="rendering" plus a running ETA — the server pipes this
        into the session progress so the user sees movement during the wait.

        Returns a complete WAV file as bytes.
        """
        import numpy as np  # local: tts module already imports soundfile

        paragraphs = [p.strip() for p in script.split("\n\n") if p.strip()]
        if not paragraphs:
            raise ValueError("empty script")

        effective_speed = speed if speed is not None else self.speed

        rendered: list[np.ndarray] = []
        sample_rate = 24000  # Kokoro outputs 24 kHz
        durations: list[float] = []
        for i, paragraph in enumerate(paragraphs):
            if on_progress is not None:
                eta = _estimate_eta(durations, total=len(paragraphs), done=i)
                on_progress(
                    stage="rendering",
                    detail=_render_detail(i + 1, len(paragraphs), eta),
                    step=i + 1,
                    total=len(paragraphs),
                    eta_seconds=eta,
                )
            t0 = time.time()
            audio, sr = self.engine.create(
                paragraph,
                voice=self.voice_name,
                speed=effective_speed,
                lang="en-us",
            )
            durations.append(time.time() - t0)
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


# ---------------------------------------------------------------------------
# F5-TTS Voice — the user's own fine-tuned voice.
# ---------------------------------------------------------------------------


@dataclass
class F5Voice:
    """The user's own voice, via a fine-tuned F5-TTS checkpoint.

    Loaded lazily; the model weights are several GB. Each generation needs
    a reference clip (a short recording from the speaker) and the text of
    that recording — F5-TTS conditions on both. Pace is roughly 1/4× to
    1/8× real-time on M3 (so a 12-min session takes ~15-20 min to render).
    """

    engine: object
    speaker: str
    ref_file: Path
    ref_text: str
    speed: float
    cfg_strength: float
    nfe_step: int

    @classmethod
    def load(cls, *, speaker: str | None = None) -> "F5Voice":
        # Import lazily — F5-TTS imports are heavy (torch, vocos, etc.)
        # and we don't want them paid unless the user actually picks
        # "your voice" at intake.
        from importlib.resources import files as _files
        from f5_tts.api import F5TTS
        from imagination_engine.config import PROJECT_ROOT

        spk = speaker or config.f5_speaker
        ckpt = Path(str(_files("f5_tts").joinpath(
            f"../../ckpts/{spk}/{config.f5_checkpoint}"
        ))).resolve()
        vocab = Path(str(_files("f5_tts").joinpath(
            "../../data/Emilia_ZH_EN_pinyin/vocab.txt"
        ))).resolve()
        ref_file = PROJECT_ROOT / "data" / "dataset" / spk / "wavs" / f"{config.f5_ref_id}.wav"

        if not ckpt.is_file():
            raise FileNotFoundError(f"F5-TTS checkpoint not found: {ckpt}")
        if not ref_file.is_file():
            raise FileNotFoundError(f"reference clip not found: {ref_file}")

        log.info("Loading F5-TTS model (%s, %s) ...", spk, config.f5_checkpoint)
        engine = F5TTS(
            model="F5TTS_v1_Base",
            ckpt_file=str(ckpt),
            vocab_file=str(vocab),
            use_ema=False,         # use the actually fine-tuned online weights
            device="mps",
        )
        log.info("F5-TTS loaded.")

        return cls(
            engine=engine,
            speaker=spk,
            ref_file=ref_file,
            ref_text=config.f5_ref_text,
            speed=config.f5_speed,
            cfg_strength=config.f5_cfg_strength,
            nfe_step=config.f5_nfe_step,
        )

    @property
    def backend(self) -> str:
        return "f5"

    @property
    def display_name(self) -> str:
        return self.speaker.capitalize()

    def speak(self, text: str, *, speed: float | None = None) -> bytes:
        """Render a single short utterance to WAV bytes."""
        import numpy as np
        audio, sample_rate, _ = self.engine.infer(
            ref_file=str(self.ref_file),
            ref_text=self.ref_text,
            gen_text=text,
            speed=speed if speed is not None else self.speed,
            seed=None,                # vary per call
            cfg_strength=self.cfg_strength,
            nfe_step=self.nfe_step,
        )
        buf = io.BytesIO()
        sf.write(buf, np.asarray(audio, dtype="float32"), sample_rate, format="WAV")
        return buf.getvalue()

    def render_session(
        self,
        script: str,
        *,
        pause_between_paragraphs: float = 2.0,
        speed: float | None = None,
        on_progress: Optional[ProgressFn] = None,
    ) -> bytes:
        """Render a full session script — paragraph-by-paragraph, with real silence between.

        F5-TTS renders at ~1/4× to 1/8× real-time on M3, so a 12-min session
        takes 15-20 minutes. `on_progress` (if supplied) fires before each
        paragraph with a running ETA computed from the actual per-paragraph
        time so far — so the user-visible "preparing" line counts down
        honestly, not from a hardcoded guess.
        """
        import numpy as np

        paragraphs = [p.strip() for p in script.split("\n\n") if p.strip()]
        if not paragraphs:
            raise ValueError("empty script")

        eff_speed = speed if speed is not None else self.speed
        sample_rate = 24000  # F5-TTS Vocos vocoder outputs 24 kHz

        rendered: list[np.ndarray] = []
        durations: list[float] = []
        for i, paragraph in enumerate(paragraphs):
            if on_progress is not None:
                eta = _estimate_eta(durations, total=len(paragraphs), done=i)
                on_progress(
                    stage="rendering",
                    detail=_render_detail(i + 1, len(paragraphs), eta),
                    step=i + 1,
                    total=len(paragraphs),
                    eta_seconds=eta,
                )
            log.info("F5 render paragraph %d/%d (%d chars)", i + 1, len(paragraphs), len(paragraph))
            t0 = time.time()
            audio, sr, _ = self.engine.infer(
                ref_file=str(self.ref_file),
                ref_text=self.ref_text,
                gen_text=paragraph,
                speed=eff_speed,
                seed=None,
                cfg_strength=self.cfg_strength,
                nfe_step=self.nfe_step,
            )
            durations.append(time.time() - t0)
            sample_rate = sr
            rendered.append(np.asarray(audio, dtype="float32"))
            if i < len(paragraphs) - 1:
                silence = np.zeros(
                    int(pause_between_paragraphs * sample_rate),
                    dtype="float32",
                )
                rendered.append(silence)

        full = np.concatenate(rendered)
        buf = io.BytesIO()
        sf.write(buf, full, sample_rate, format="WAV")
        return buf.getvalue()


# ---------------------------------------------------------------------------
# Progress helpers — shared between Kokoro and F5 render paths.
# ---------------------------------------------------------------------------


def _estimate_eta(durations: list[float], *, total: int, done: int) -> float | None:
    """Project the remaining render time from per-paragraph timings so far.

    First paragraph: no data yet → return None. After that, average the
    completed paragraph durations and multiply by paragraphs remaining.
    Honest projection beats a hardcoded guess, especially on F5 where the
    first paragraph is slow (warm-up) and later ones settle into a rhythm.
    """
    remaining = total - done
    if remaining <= 0:
        return 0.0
    if not durations:
        return None
    avg = sum(durations) / len(durations)
    return avg * remaining


def _render_detail(current: int, total: int, eta_seconds: float | None) -> str:
    """User-facing detail line for the rendering stage."""
    base = f"Rendering paragraph {current} of {total}"
    if eta_seconds is None:
        return base + "."
    if eta_seconds < 90:
        return f"{base}. About {max(int(round(eta_seconds)), 5)} seconds left."
    minutes = int(round(eta_seconds / 60))
    return f"{base}. About {minutes} minute{'s' if minutes != 1 else ''} left."


# ---------------------------------------------------------------------------
# Chatterbox-TTS Voice — the two curated "system voices" (her / him).
# ---------------------------------------------------------------------------


# Names of the two curated voices and where their reference clips live.
SYSTEM_VOICE_NAMES = ("her", "him")


@dataclass
class ChatterboxVoice:
    """A curated system voice via Resemble AI's Chatterbox (MIT-licensed).

    Zero-shot cloned from a 10-15s reference clip. Chosen by the founder as
    the two first-class non-user voices for v0 — one warm woman, one slow
    measured man — tuned for the "intimate audiobook narrator" feel that
    works for a 12-minute eyes-closed session.

    Two operational quirks of Chatterbox:
      1. Single-pass generation caps at ~40 seconds of audio. We chunk at
         paragraph boundaries first (preserving the breath-pauses the script
         encodes via blank lines), and sub-split any long paragraph at
         sentence boundaries with a tiny crossfade between sub-chunks.
      2. Every output is embedded with Resemble's PerTh neural watermark.
         Not a license restriction; documented here so it's not a surprise.
    """

    engine: object              # chatterbox.tts.ChatterboxTTS
    name: str                   # "her" | "him"
    ref_file: Path              # the 10-15s reference clip
    exaggeration: float
    cfg_weight: float
    temperature: float
    max_words_per_chunk: int
    crossfade_ms: int
    sample_rate: int            # detected at load time from the engine

    @classmethod
    def load(cls, *, name: str) -> "ChatterboxVoice":
        from imagination_engine.config import (
            SYSTEM_VOICES_DIR,
        )

        n = name.lower().strip()
        if n not in SYSTEM_VOICE_NAMES:
            raise ValueError(
                f"unknown system voice {name!r} — must be one of {SYSTEM_VOICE_NAMES}"
            )

        ref_file = SYSTEM_VOICES_DIR / f"{n}.wav"
        if not ref_file.is_file():
            raise FileNotFoundError(
                f"reference clip not found: {ref_file}. "
                f"Run scripts/download_system_voices.py to source it, "
                f"or drop a 10-15s WAV at that path."
            )

        # Lazy import — chatterbox pulls torch, diffusers, etc.
        from chatterbox.tts import ChatterboxTTS

        log.info("Loading Chatterbox system voice (%s) ...", n)
        engine = ChatterboxTTS.from_pretrained(device="mps")
        # Chatterbox exposes its native sample rate as engine.sr.
        sr = getattr(engine, "sr", 24000)
        log.info("Chatterbox loaded (sample_rate=%d).", sr)

        return cls(
            engine=engine,
            name=n,
            ref_file=ref_file,
            exaggeration=config.chatterbox_exaggeration,
            cfg_weight=config.chatterbox_cfg_weight,
            temperature=config.chatterbox_temperature,
            max_words_per_chunk=config.chatterbox_max_words_per_chunk,
            crossfade_ms=config.chatterbox_crossfade_ms,
            sample_rate=sr,
        )

    @property
    def backend(self) -> str:
        return "chatterbox"

    @property
    def speaker(self) -> str:
        return self.name

    @property
    def display_name(self) -> str:
        return {"her": "Her", "him": "Him"}.get(self.name, self.name.capitalize())

    # ---- Chunking ---------------------------------------------------------

    def _split_paragraph(self, paragraph: str) -> list[str]:
        """Split a single paragraph into Chatterbox-safe word-budgeted chunks.

        Respects sentence boundaries — never mid-sentence. Single-sentence
        paragraphs longer than the budget are rare in our scripts but if
        they happen, fall through to a single-element list (the engine will
        truncate; we accept that as a known-rare failure rather than splitting
        mid-sentence which would audibly break the listening experience).
        """
        import re

        words = paragraph.split()
        if len(words) <= self.max_words_per_chunk:
            return [paragraph]

        sentences = re.split(r"(?<=[.!?])\s+", paragraph)
        chunks: list[str] = []
        current: list[str] = []
        current_words = 0
        for s in sentences:
            sw = len(s.split())
            if current and current_words + sw > self.max_words_per_chunk:
                chunks.append(" ".join(current))
                current = [s]
                current_words = sw
            else:
                current.append(s)
                current_words += sw
        if current:
            chunks.append(" ".join(current))
        return chunks

    def _crossfade_concat(self, segments: "list", sample_rate: int):
        """Concatenate sub-paragraph audio segments with a short crossfade.

        Used only when a single paragraph had to be split for the 40-sec cap;
        the crossfade hides the chunk boundary inside what the listener
        experiences as one continuous paragraph. Real silence between full
        paragraphs is handled separately, outside this helper.
        """
        import numpy as np

        if not segments:
            return np.zeros(0, dtype=np.float32)
        if len(segments) == 1:
            return segments[0]

        fade_samples = int(self.crossfade_ms / 1000.0 * sample_rate)
        if fade_samples <= 0:
            return np.concatenate(segments)

        result = segments[0].copy()
        fade_out = np.linspace(1.0, 0.0, fade_samples, dtype=np.float32)
        fade_in = np.linspace(0.0, 1.0, fade_samples, dtype=np.float32)
        for nxt in segments[1:]:
            if len(result) < fade_samples or len(nxt) < fade_samples:
                # Too short to crossfade — just butt-join.
                result = np.concatenate([result, nxt])
                continue
            result[-fade_samples:] = result[-fade_samples:] * fade_out + nxt[:fade_samples] * fade_in
            result = np.concatenate([result, nxt[fade_samples:]])
        return result

    # ---- One-shot ---------------------------------------------------------

    def speak(self, text: str, *, speed: float | None = None) -> bytes:
        """Render a single short utterance to WAV bytes. `speed` is ignored;
        Chatterbox doesn't expose a direct speed knob (use `temperature` for
        natural variation). Provided for parity with the Voice interface."""
        import numpy as np

        wav = self.engine.generate(
            text,
            audio_prompt_path=str(self.ref_file),
            exaggeration=self.exaggeration,
            cfg_weight=self.cfg_weight,
            temperature=self.temperature,
        )
        arr = _to_float32_mono(wav)
        buf = io.BytesIO()
        sf.write(buf, arr, self.sample_rate, format="WAV")
        return buf.getvalue()

    # ---- Full session -----------------------------------------------------

    def render_session(
        self,
        script: str,
        *,
        pause_between_paragraphs: float = 2.0,
        speed: float | None = None,
        on_progress: Optional[ProgressFn] = None,
    ) -> bytes:
        """Render a full session script.

        Two-level chunking: paragraphs are the primary boundary (preserving
        the breath-pauses the script encoded via blank lines), and within
        each paragraph we sub-chunk if needed to stay under Chatterbox's
        40-sec cap. `on_progress` fires before each chunk render with a
        running ETA computed from per-chunk durations so far.
        """
        import numpy as np

        paragraphs = [p.strip() for p in script.split("\n\n") if p.strip()]
        if not paragraphs:
            raise ValueError("empty script")

        # First pass: pre-chunk all paragraphs so we know the total count up
        # front for honest progress reporting (the user sees "chunk 7 of 30").
        paragraph_chunks: list[list[str]] = [self._split_paragraph(p) for p in paragraphs]
        total_chunks = sum(len(c) for c in paragraph_chunks)

        rendered: list = []
        durations: list[float] = []
        completed = 0

        for p_idx, chunks in enumerate(paragraph_chunks):
            segments: list = []
            for c_idx, chunk in enumerate(chunks):
                if on_progress is not None:
                    eta = _estimate_eta(durations, total=total_chunks, done=completed)
                    detail = (
                        f"Rendering paragraph {p_idx + 1} of {len(paragraphs)}"
                        + (f" (part {c_idx + 1} of {len(chunks)})" if len(chunks) > 1 else "")
                    )
                    if eta is not None:
                        if eta < 90:
                            detail += f". About {max(int(round(eta)), 5)} seconds left."
                        else:
                            mins = int(round(eta / 60))
                            detail += f". About {mins} minute{'s' if mins != 1 else ''} left."
                    else:
                        detail += "."
                    on_progress(
                        stage="rendering",
                        detail=detail,
                        step=completed + 1,
                        total=total_chunks,
                        eta_seconds=eta,
                    )

                log.info(
                    "Chatterbox render p%d/%d chunk %d/%d (%d words)",
                    p_idx + 1, len(paragraphs), c_idx + 1, len(chunks), len(chunk.split()),
                )
                t0 = time.time()
                wav = self.engine.generate(
                    chunk,
                    audio_prompt_path=str(self.ref_file),
                    exaggeration=self.exaggeration,
                    cfg_weight=self.cfg_weight,
                    temperature=self.temperature,
                )
                durations.append(time.time() - t0)
                completed += 1
                segments.append(_to_float32_mono(wav))

            # Stitch sub-chunks of this paragraph (crossfade if multi-chunk).
            paragraph_audio = self._crossfade_concat(segments, self.sample_rate)
            rendered.append(paragraph_audio)

            # Real silence between full paragraphs — the listener's breath.
            if p_idx < len(paragraphs) - 1:
                silence = np.zeros(
                    int(pause_between_paragraphs * self.sample_rate),
                    dtype="float32",
                )
                rendered.append(silence)

        full = np.concatenate(rendered)
        buf = io.BytesIO()
        sf.write(buf, full, self.sample_rate, format="WAV")
        return buf.getvalue()


def _to_float32_mono(wav) -> "np.ndarray":
    """Normalize a Chatterbox return value into a 1-D float32 numpy array.

    Chatterbox returns a torch tensor of shape (channels, samples) — we want
    mono float32 samples for soundfile.write. Defensive about dimensionality
    in case the library shape ever changes.
    """
    import numpy as np

    if hasattr(wav, "detach"):  # torch tensor
        wav = wav.detach().cpu().numpy()
    arr = np.asarray(wav, dtype="float32")
    while arr.ndim > 1:
        arr = arr.squeeze(0) if arr.shape[0] == 1 else arr.mean(axis=0)
    return arr


# ---------------------------------------------------------------------------
# Factory — picks the backend by name.
# ---------------------------------------------------------------------------


def make_voice(backend: str = "her"):
    """Return a loaded Voice instance for the requested backend.

    backend = "her"     → Chatterbox curated woman voice (system voice)
    backend = "him"     → Chatterbox curated man voice (system voice)
    backend = "f5"      → F5Voice (the user's own fine-tuned voice)
    backend = "kokoro"  → Legacy Kokoro, retained only for the /dev surface
    """
    b = backend.lower().strip()
    if b in ("her", "she", "woman", "elizabeth"):
        return ChatterboxVoice.load(name="her")
    if b in ("him", "he", "man", "mark"):
        return ChatterboxVoice.load(name="him")
    if b in ("f5", "f5-tts", "sonali", "yours", "own"):
        return F5Voice.load()
    if b == "kokoro":
        return Voice.load()
    raise ValueError(f"unknown voice backend: {backend!r}")
