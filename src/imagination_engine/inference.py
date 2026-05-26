"""Local inference engine — the seam between an open-source primitive and our product.

Wraps `mlx-lm` (Apple's open-source MLX inference library, MIT) to expose a
small, owned `Engine` interface. We use mlx-lm directly — no third-party
orchestrator (Ollama, LM Studio, etc.) between us and the weights. Model
weights are fetched directly from Hugging Face.

Future swaps — a different model, llama.cpp instead of MLX, a fine-tune —
happen here, without touching the protocol or server layers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

from mlx_lm import load, stream_generate
from mlx_lm.sample_utils import make_sampler

from imagination_engine.config import config


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
    def load(cls, model_id: str | None = None) -> "Engine":
        mid = model_id or config.model_id
        model, tokenizer = load(mid)
        return cls(model=model, tokenizer=tokenizer, model_id=mid)

    def stream(
        self,
        prompt: str,
        *,
        max_tokens: int | None = None,
        temperature: float | None = None,
        system: str | None = None,
    ) -> Iterator[str]:
        """Stream the model's response to `prompt`, yielding text chunks.

        Applies the tokenizer's chat template so the instruction-tuned model
        receives a properly formatted conversation, not a raw string.
        """
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        formatted = self.tokenizer.apply_chat_template(
            messages, add_generation_prompt=True, tokenize=False
        )

        sampler = make_sampler(
            temp=temperature if temperature is not None else config.temperature,
        )

        for response in stream_generate(
            self.model,
            self.tokenizer,
            prompt=formatted,
            max_tokens=max_tokens or config.max_tokens,
            sampler=sampler,
        ):
            yield response.text
