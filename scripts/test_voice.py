"""Test the fine-tuned F5-TTS voice on a sentence the model never saw.

Loads the latest fine-tune checkpoint for a speaker and generates a
short audio sample. The model also needs a reference clip from the
speaker to anchor the timbre — we use one of their recordings.

Usage:
    uv run python scripts/test_voice.py <speaker_id> [--checkpoint model_200.pt]
"""

from __future__ import annotations

import argparse
import sys
import time
from importlib.resources import files
from pathlib import Path

from f5_tts.api import F5TTS

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = PROJECT_ROOT / "logs" / "voice-tests"

# Reference clip + transcript. A short, clean, calm Sonali line. Using one of
# the guided-imagery recordings keeps the model in the right register.
DEFAULT_REF = {
    "sonali": {
        "ref_id": "i005",
        "ref_text": "Just this breath. Just this one breath.",
    },
}

# Sentences the model did NOT see in training (different wording from the
# recording script) — so we hear *generation*, not regurgitation.
DEFAULT_GEN_TEXTS = [
    "Let your breath slow. Notice the small sounds of the morning. There is nowhere you need to be.",
    "Picture yourself, a year from now, walking through a room you love.",
    "Settle into the chair. Feel the weight of the day fall away from your shoulders.",
]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("speaker", help="speaker id (e.g. sonali)")
    p.add_argument("--checkpoint", default="model_200.pt",
                   help="checkpoint file in .venv/lib/python3.13/ckpts/<speaker>/")
    p.add_argument("--use-ema", action="store_true",
                   help="use EMA shadow weights (default off: use the actually fine-tuned online weights)")
    args = p.parse_args()

    ckpt_dir = Path(str(files("f5_tts").joinpath(f"../../ckpts/{args.speaker}"))).resolve()
    ckpt_file = ckpt_dir / args.checkpoint
    vocab_file = Path(str(files("f5_tts").joinpath("../../data/Emilia_ZH_EN_pinyin/vocab.txt"))).resolve()

    if not ckpt_file.is_file():
        print(f"[error] no checkpoint at {ckpt_file}")
        return 1
    if not vocab_file.is_file():
        print(f"[error] no vocab at {vocab_file}")
        return 1

    ref_meta = DEFAULT_REF.get(args.speaker)
    if not ref_meta:
        print(f"[error] no default reference configured for {args.speaker}")
        return 1
    ref_file = PROJECT_ROOT / "data" / "dataset" / args.speaker / "wavs" / f"{ref_meta['ref_id']}.wav"
    if not ref_file.is_file():
        print(f"[error] no reference audio at {ref_file}")
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"speaker:     {args.speaker}")
    print(f"checkpoint:  {ckpt_file}  ({ckpt_file.stat().st_size / (1024**3):.1f} GB)")
    print(f"vocab:       {vocab_file}")
    print(f"reference:   {ref_file.name}  ({ref_meta['ref_text']!r})")
    print(f"use_ema:     {args.use_ema}")
    print(f"output dir:  {OUT_DIR}")
    print()

    print("Loading model ...")
    t0 = time.time()
    f5 = F5TTS(
        model="F5TTS_v1_Base",
        ckpt_file=str(ckpt_file),
        vocab_file=str(vocab_file),
        use_ema=args.use_ema,
        device="mps",
    )
    print(f"  loaded in {time.time()-t0:.1f}s")
    print()

    for i, gen_text in enumerate(DEFAULT_GEN_TEXTS, start=1):
        suffix = "ema" if args.use_ema else "online"
        out_path = OUT_DIR / f"{args.speaker}_{args.checkpoint.replace('.pt','')}_{suffix}_{i:02d}.wav"
        print(f"[{i}/{len(DEFAULT_GEN_TEXTS)}] {gen_text!r}")
        t0 = time.time()
        f5.infer(
            ref_file=str(ref_file),
            ref_text=ref_meta["ref_text"],
            gen_text=gen_text,
            file_wave=str(out_path),
            seed=42 + i,
            cfg_strength=2.0,
            nfe_step=32,
        )
        print(f"  wrote {out_path.name}  ({time.time()-t0:.1f}s)")
        print()

    print(f"Done. Play with: afplay {OUT_DIR}/<file>.wav")
    return 0


if __name__ == "__main__":
    sys.exit(main())
