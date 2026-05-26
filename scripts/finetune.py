"""Fine-tune F5-TTS on a speaker's recorded dataset.

A small driver that calls F5-TTS's `Trainer` class directly with
memory-friendly hyperparameters tuned for a 16 GB Apple Silicon Mac.
We don't use `f5_tts.train.finetune_cli` because it doesn't expose
`accelerate_kwargs` (so no fp16 mixed precision) or `ema_kwargs`.

Usage:
    uv run python scripts/finetune.py <speaker_id> [--batch N] [--grad-accum N]
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from importlib.resources import files
from pathlib import Path

from cached_path import cached_path

from f5_tts.model import CFM, DiT, Trainer
from f5_tts.model.dataset import load_dataset
from f5_tts.model.utils import get_tokenizer

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Audio/model constants — match F5TTS_v1_Base.
TARGET_SAMPLE_RATE = 24000
N_MEL_CHANNELS = 100
HOP_LENGTH = 256
WIN_LENGTH = 1024
N_FFT = 1024
MEL_SPEC_TYPE = "vocos"

# F5TTS_v1_Base architecture.
MODEL_CFG = dict(
    dim=1024,
    depth=22,
    heads=16,
    ff_mult=2,
    text_dim=512,
    conv_layers=4,
)
PRETRAINED_CKPT = "hf://SWivid/F5-TTS/F5TTS_v1_Base/model_1250000.safetensors"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("speaker", help="speaker id (e.g. sonali)")
    p.add_argument("--batch", type=int, default=400,
                   help="batch_size_per_gpu in audio frames (default 400 — small for 16 GB M3)")
    p.add_argument("--grad-accum", type=int, default=4,
                   help="gradient accumulation steps (effective batch = batch * grad_accum)")
    p.add_argument("--max-samples", type=int, default=8,
                   help="max sequences per batch (default 8)")
    p.add_argument("--lr", type=float, default=1e-5)
    p.add_argument("--epochs", type=int, default=100)
    p.add_argument("--warmup", type=int, default=50)
    p.add_argument("--save-every", type=int, default=200,
                   help="save full checkpoint every N updates")
    p.add_argument("--last-every", type=int, default=100,
                   help="save 'last' checkpoint every N updates")
    p.add_argument("--mixed-precision", default="fp16",
                   choices=["no", "fp16", "bf16"],
                   help="mixed-precision mode for accelerate (fp16 ~halves activation memory)")
    p.add_argument("--log-samples", action="store_true",
                   help="generate inference samples at each checkpoint (uses extra memory)")
    args = p.parse_args()

    speaker = args.speaker
    tokenizer = "pinyin"

    # Checkpoint output dir — F5-TTS' load/save assumes ../../ckpts/{name} from
    # the package install location. We mirror that convention so resume works.
    checkpoint_path = str(files("f5_tts").joinpath(f"../../ckpts/{speaker}"))
    os.makedirs(checkpoint_path, exist_ok=True)

    # Make sure the pretrained checkpoint is in the expected place.
    ckpt_src = str(cached_path(PRETRAINED_CKPT))
    ckpt_dst = os.path.join(checkpoint_path, "pretrained_" + os.path.basename(ckpt_src))
    if not os.path.isfile(ckpt_dst):
        print(f"copying pretrained checkpoint → {ckpt_dst}")
        shutil.copy2(ckpt_src, ckpt_dst)

    # Vocab.
    vocab_char_map, vocab_size = get_tokenizer(speaker, tokenizer)
    print(f"vocab size: {vocab_size}")

    mel_spec_kwargs = dict(
        n_fft=N_FFT,
        hop_length=HOP_LENGTH,
        win_length=WIN_LENGTH,
        n_mel_channels=N_MEL_CHANNELS,
        target_sample_rate=TARGET_SAMPLE_RATE,
        mel_spec_type=MEL_SPEC_TYPE,
    )

    model = CFM(
        transformer=DiT(**MODEL_CFG, text_num_embeds=vocab_size, mel_dim=N_MEL_CHANNELS),
        mel_spec_kwargs=mel_spec_kwargs,
        vocab_char_map=vocab_char_map,
    )

    # Accelerate kwargs: enable fp16 mixed precision to halve activation memory.
    accelerate_kwargs = {}
    if args.mixed_precision != "no":
        accelerate_kwargs["mixed_precision"] = args.mixed_precision

    print(
        f"batch_size_per_gpu={args.batch}  "
        f"grad_accum={args.grad_accum}  "
        f"effective_batch={args.batch * args.grad_accum}  "
        f"max_samples={args.max_samples}  "
        f"mixed_precision={args.mixed_precision}"
    )

    trainer = Trainer(
        model,
        epochs=args.epochs,
        learning_rate=args.lr,
        num_warmup_updates=args.warmup,
        save_per_updates=args.save_every,
        keep_last_n_checkpoints=2,
        checkpoint_path=checkpoint_path,
        batch_size_per_gpu=args.batch,
        batch_size_type="frame",
        max_samples=args.max_samples,
        grad_accumulation_steps=args.grad_accum,
        max_grad_norm=1.0,
        logger=None,
        log_samples=args.log_samples,
        last_per_updates=args.last_every,
        accelerate_kwargs=accelerate_kwargs,
        bnb_optimizer=False,
        mel_spec_type=MEL_SPEC_TYPE,
    )

    train_dataset = load_dataset(speaker, tokenizer, mel_spec_kwargs=mel_spec_kwargs)
    trainer.train(train_dataset, resumable_with_seed=666)
    return 0


if __name__ == "__main__":
    sys.exit(main())
