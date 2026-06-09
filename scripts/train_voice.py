#!/usr/bin/env python3
"""Train a user's OWN voice from their /record clips — the end-to-end trainer.

Chains the three steps that were previously manual CLI-only:
  1. prepare_dataset.py <speaker>            (clips -> 24kHz wavs + metadata.csv)
  2. f5_tts ... prepare_csv_wavs             (metadata.csv -> Arrow dataset)
  3. finetune.py <speaker>                   (F5-TTS fine-tune -> checkpoint)
Writes a status JSON the UI polls, and on success registers the voice in
data/voices.json so the "Your own voice" option becomes usable.

Usage: python scripts/train_voice.py <speaker_id> [--epochs N]
This is the thing a non-technical user triggers with one button; it runs in the
background (it's long — tens of minutes to overnight on a 16GB Mac).
"""
from __future__ import annotations
import argparse, json, os, subprocess, sys, time, glob
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable
DATA = ROOT / "data"
STATUS_DIR = DATA / "voice_training"; STATUS_DIR.mkdir(parents=True, exist_ok=True)

def status_path(speaker): return STATUS_DIR / f"{speaker}.json"

def write_status(speaker, **kw):
    p = status_path(speaker)
    cur = json.loads(p.read_text()) if p.exists() else {}
    cur.update(kw); cur["speaker"] = speaker; cur["updated"] = time.time()
    p.write_text(json.dumps(cur, indent=2))

def run(cmd, speaker, stage, log):
    write_status(speaker, stage=stage, state="running", error=None)
    with open(log, "a") as lf:
        lf.write(f"\n\n===== {stage}: {' '.join(cmd)} =====\n")
        r = subprocess.run(cmd, cwd=str(ROOT), stdout=lf, stderr=subprocess.STDOUT)
    if r.returncode != 0:
        write_status(speaker, state="error", error=f"{stage} failed (exit {r.returncode}) — see {log.name}")
        raise SystemExit(f"{stage} failed")

def main(speaker, epochs):
    log = STATUS_DIR / f"{speaker}.log"
    write_status(speaker, state="running", stage="starting", started=time.time(),
                 message="Preparing your recordings…", error=None, done=False)

    # 1. clips -> wavs + metadata.csv
    run([PY, "scripts/prepare_dataset.py", speaker], speaker, "prepare_dataset", log)

    # 2. metadata.csv -> Arrow dataset (F5 format)
    meta = DATA / "dataset" / speaker / "metadata.csv"
    out_arrow = DATA / "dataset" / f"{speaker}_pinyin"
    run([PY, "-m", "f5_tts.train.datasets.prepare_csv_wavs", str(meta), str(out_arrow)],
        speaker, "build_dataset", log)

    # 3. fine-tune F5 on the speaker
    write_status(speaker, stage="training", state="running",
                 message="Training your voice — this takes a while. You can leave; it keeps going.")
    run([PY, "scripts/finetune.py", speaker, "--epochs", str(epochs)], speaker, "training", log)

    # locate the trained checkpoint + register the voice
    from importlib.resources import files as _files
    ckdir = Path(str(_files("f5_tts").joinpath(f"../../ckpts/{speaker}"))).resolve()
    ckpts = sorted(glob.glob(str(ckdir / "model_*.pt")), key=os.path.getmtime)
    ckpts = [c for c in ckpts if "pretrained" not in os.path.basename(c)]
    if not ckpts:
        write_status(speaker, state="error", error="training finished but no checkpoint found")
        raise SystemExit("no checkpoint")
    ckpt = os.path.basename(ckpts[-1])

    voices = DATA / "voices.json"
    reg = json.loads(voices.read_text()) if voices.exists() else {}
    reg["own"] = {"speaker": speaker, "checkpoint": ckpt, "trained_at": time.time()}
    voices.write_text(json.dumps(reg, indent=2))

    write_status(speaker, state="done", stage="done", done=True, checkpoint=ckpt,
                 message="Your voice is ready. Choose it in any session.")
    print(f"voice trained + registered: {speaker} / {ckpt}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("speaker")
    ap.add_argument("--epochs", type=int, default=100)
    a = ap.parse_args()
    main(a.speaker, a.epochs)
