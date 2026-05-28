"""Re-render the fine-tuned voice with different reference clips and speeds.

The first round (test_voice.py) used a slow guided-imagery reference (i005)
at speed 0.9 (config default). The output sounded slow + nonconversational.
This script tests two hypotheses:

  1. Reference clip controls a lot of the pace. Using a conversational
     reference (g021 — narrative, mid-energy) should produce a less
     measured cadence even for the same text.
  2. Speed parameter (independent of reference) bumps the actual rate.
     speed=1.0 vs 0.9 makes a noticeable difference.

Outputs go to logs/voice-tests/round2/ so the comparison is easy.
"""

from __future__ import annotations

import json
import time
from importlib.resources import files
from pathlib import Path

from f5_tts.api import F5TTS

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = PROJECT_ROOT / "logs" / "voice-tests" / "round2"
SPEAKER = "sonali"

# Reference clip options (all in data/dataset/sonali/wavs/):
# - i005 (original, slow guided-imagery)            "Just this breath. Just this one breath."
# - g021 (conversational, narrative)                "The dog dropped the rope at her feet and looked up, plainly waiting."
# - h005 (Harvard, neutral)                         "Rice is often served in round bowls."

REFERENCES = {
    "i005": "Just this breath. Just this one breath.",
    "g021": "The dog dropped the rope at her feet and looked up, plainly waiting.",
    "h005": "Rice is often served in round bowls.",
}

# Combinations to render: (label, ref_id, ref_text, speed, gen_text)
COMBINATIONS = [
    # Same guided sentences as round 1, but with a more conversational reference + speed 1.0
    ("guided-fastref-s10-01", "g021", REFERENCES["g021"], 1.0,
     "Let your breath slow. Notice the small sounds of the morning. There is nowhere you need to be."),
    ("guided-fastref-s10-02", "g021", REFERENCES["g021"], 1.0,
     "Picture yourself, a year from now, walking through a room you love."),
    ("guided-fastref-s10-03", "g021", REFERENCES["g021"], 1.0,
     "Settle into the chair. Feel the weight of the day fall away from your shoulders."),

    # Same content with even faster speed
    ("guided-fastref-s11-01", "g021", REFERENCES["g021"], 1.1,
     "Let your breath slow. Notice the small sounds of the morning. There is nowhere you need to be."),

    # Conversational text + conversational reference — what does your voice sound like in everyday speech?
    ("conversational-01", "g021", REFERENCES["g021"], 1.0,
     "Hey, so I was thinking we should get tacos tonight. Are you in?"),
    ("conversational-02", "g021", REFERENCES["g021"], 1.0,
     "Yeah, that's the thing. I never told her how I actually felt."),
    ("conversational-03", "g021", REFERENCES["g021"], 1.05,
     "Okay so picture this — you walk in and the whole room just stops. Total quiet."),
]

CKPT_DIR = Path(str(files("f5_tts").joinpath("../../ckpts/sonali"))).resolve()
CKPT_FILE = CKPT_DIR / "model_3000.pt"  # bumped from model_200 after the v2 training run
VOCAB_FILE = Path(str(files("f5_tts").joinpath("../../data/Emilia_ZH_EN_pinyin/vocab.txt"))).resolve()


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Loading fine-tuned F5-TTS (model_200) ...")
    t0 = time.time()
    f5 = F5TTS(
        model="F5TTS_v1_Base",
        ckpt_file=str(CKPT_FILE),
        vocab_file=str(VOCAB_FILE),
        use_ema=False,
        device="mps",
    )
    print(f"  loaded in {time.time()-t0:.1f}s")
    print()

    manifest = []
    for label, ref_id, ref_text, speed, gen_text in COMBINATIONS:
        ref_file = PROJECT_ROOT / "data" / "dataset" / SPEAKER / "wavs" / f"{ref_id}.wav"
        out_path = OUT_DIR / f"{label}.wav"
        print(f"[{label}] ref={ref_id} speed={speed}")
        print(f"  text: {gen_text!r}")
        t0 = time.time()
        f5.infer(
            ref_file=str(ref_file),
            ref_text=ref_text,
            gen_text=gen_text,
            file_wave=str(out_path),
            speed=speed,
            seed=42,
            cfg_strength=2.0,
            nfe_step=32,
        )
        elapsed = time.time() - t0
        print(f"  wrote {out_path.name} ({elapsed:.1f}s)")
        print()
        manifest.append({
            "file": out_path.name,
            "ref_id": ref_id,
            "speed": speed,
            "text": gen_text,
            "render_seconds": round(elapsed, 1),
        })

    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Done. {len(manifest)} samples in {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
