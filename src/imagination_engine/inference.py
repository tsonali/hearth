"""Local inference engine — the seam between an open-source primitive and our product.

Wraps `mlx-lm` (Apple's open-source MLX inference library, MIT) to expose a
small, owned `Engine` interface. We use mlx-lm directly — no third-party
orchestrator (Ollama, LM Studio, etc.) between us and the weights. Model
weights are fetched directly from Hugging Face.

Future swaps — a different model, llama.cpp instead of MLX, a fine-tune —
happen here, without touching the protocol or server layers.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Iterator

import mlx.core as mx
from mlx_lm import load, stream_generate
from mlx_lm.sample_utils import apply_top_p, make_logits_processors

from imagination_engine.config import config


def _make_seeded_sampler(*, temp: float, top_p: float, seed: int):
    """Build a sampler with an explicit per-call RNG key.

    mlx-lm's stock `make_sampler` builds a sampler around `categorical_sampling`,
    which is `@mx.compile`-decorated with `inputs=mx.random.state`. That
    compile traces and caches at first invocation in a process, fixing the
    RNG path — subsequent calls give identical output for identical prompts
    no matter how often we re-seed the global state. The clean fix is to
    skip the compiled sampler and thread an explicit key through ourselves.
    """
    key = mx.random.key(seed)

    def sampler(logprobs):
        nonlocal key
        key, subkey = mx.random.split(key)
        if 0 < top_p < 1.0:
            logprobs = apply_top_p(logprobs, top_p)
        return mx.random.categorical(logprobs * (1.0 / temp), key=subkey)

    return sampler


@dataclass
class Engine:
    """A loaded local model, ready to generate text.

    Construct via `Engine.load()`. Holds the MLX model and tokenizer in
    memory; one instance per process is the intended usage.
    """

    model: object
    tokenizer: object
    model_id: str

    @classmethod
    def load(cls, model_id: str | None = None,
             adapter_path: str | None = None) -> "Engine":
        """Load the base model, optionally with our LoRA adapter on top.

        `adapter_path` (a directory with adapters.safetensors) makes Hearth run on
        OUR fine-tuned specialist instead of stock Qwen. Falls back to base if the
        adapter is missing or fails to load — the product must always start.
        """
        import logging
        from pathlib import Path
        mid = model_id or config.model_id
        ap = adapter_path if adapter_path is not None else getattr(config, "adapter_path", None)
        if ap and Path(ap).expanduser().is_dir() and any(Path(ap).expanduser().glob("*.safetensors")):
            try:
                model, tokenizer = load(mid, adapter_path=str(Path(ap).expanduser()))
                logging.getLogger(__name__).info("loaded with LoRA adapter: %s", ap)
                return cls(model=model, tokenizer=tokenizer, model_id=mid)
            except Exception as e:
                logging.getLogger(__name__).warning(
                    "adapter load failed (%s) — falling back to base model", e)
        model, tokenizer = load(mid)
        return cls(model=model, tokenizer=tokenizer, model_id=mid)

    def stream(
        self,
        prompt: str | None = None,
        *,
        messages: list[dict[str, str]] | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        system: str | None = None,
    ) -> Iterator[str]:
        """Stream the model's response, yielding text chunks.

        Two calling conventions:
          - Single-turn: pass `prompt` (and optionally `system`).
          - Multi-turn: pass `messages` — a list of {role, content} dicts
            in the chat-completion format. Used by the intake conversation
            layer to feed full history each turn.
        """
        if messages is None and prompt is None:
            raise ValueError("pass either `prompt` or `messages`")
        if messages is None:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

        formatted = self.tokenizer.apply_chat_template(
            messages, add_generation_prompt=True, tokenize=False
        )

        # Per-call sampler with an explicit RNG seed. See `_make_seeded_sampler`
        # for why we bypass mlx-lm's stock `make_sampler` (compile-state issue).
        sampler = _make_seeded_sampler(
            temp=temperature if temperature is not None else config.temperature,
            top_p=config.top_p,
            seed=time.time_ns() & 0xFFFFFFFF,
        )

        # Repetition penalty — the fix for degenerate "word word word..." loops.
        logits_processors = make_logits_processors(
            repetition_penalty=config.repetition_penalty,
            repetition_context_size=config.repetition_context_size,
        )

        for response in stream_generate(
            self.model,
            self.tokenizer,
            prompt=formatted,
            max_tokens=max_tokens or config.max_tokens,
            sampler=sampler,
            logits_processors=logits_processors,
        ):
            yield response.text
