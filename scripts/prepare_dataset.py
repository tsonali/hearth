"""Prepare a speaker's recordings for F5-TTS fine-tuning.

Reads raw recordings from data/recordings/<speaker>/<sentence_id>.wav,
joins each with its transcript from data/recording-script.json, applies
light cleanup (resample to 24 kHz mono, peak-normalize, trim runaway
silence), and writes processed WAVs + metadata.csv into
data/dataset/<speaker>/.

The CSV is the input expected by F5-TTS' `prepare_csv_wavs.py` script,
which builds the Arrow dataset the trainer consumes.

Usage:
    uv run python scripts/prepare_dataset.py <speaker_id>
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_FILE = PROJECT_ROOT / "data" / "recording-script.json"
RECORDINGS_DIR = PROJECT_ROOT / "data" / "recordings"
DATASET_DIR = PROJECT_ROOT / "data" / "dataset"

TARGET_SR = 24000
PEAK_TARGET = 0.95              # peak amplitude after normalize (leaves ~0.4 dB headroom)
SILENCE_THRESHOLD = 0.005       # relative amplitude under which samples are considered silent
PAD_MS = 100                    # silence padding kept on both ends


def trim_silence(samples: np.ndarray, sr: int, thresh: float, pad_ms: int) -> np.ndarray:
    """Trim runaway leading/trailing silence; leave `pad_ms` of margin on each end."""
    above = np.abs(samples) > thresh
    if not above.any():
        return samples
    pad = int(pad_ms / 1000 * sr)
    first = int(np.argmax(above))
    last = len(samples) - int(np.argmax(above[::-1]))
    start = max(0, first - pad)
    end = min(len(samples), last + pad)
    return samples[start:end]


def peak_normalize(samples: np.ndarray, target: float) -> np.ndarray:
    peak = float(np.max(np.abs(samples)))
    if peak < 1e-9:
        return samples
    return samples * (target / peak)


def _gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a


def process_one(in_path: Path, out_path: Path) -> float:
    """Returns duration of the output WAV in seconds."""
    samples, sr = sf.read(str(in_path), dtype="float32", always_2d=False)
    if samples.ndim == 2:                          # downmix any stereo
        samples = samples.mean(axis=1)
    if sr != TARGET_SR:
        # Polyphase resampling — high quality, fast, pure scipy.
        g = _gcd(int(sr), TARGET_SR)
        up = TARGET_SR // g
        down = int(sr) // g
        samples = resample_poly(samples, up, down).astype(np.float32)
    samples = trim_silence(samples, TARGET_SR, SILENCE_THRESHOLD, PAD_MS)
    samples = peak_normalize(samples, PEAK_TARGET)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(out_path), samples, TARGET_SR, subtype="PCM_16")
    return len(samples) / TARGET_SR


def main(speaker: str) -> int:
    if not SCRIPT_FILE.exists():
        print(f"[error] {SCRIPT_FILE} not found", file=sys.stderr)
        return 1
    sentences = {s["id"]: s for s in json.loads(SCRIPT_FILE.read_text())["sentences"]}

    src_dir = RECORDINGS_DIR / speaker
    if not src_dir.is_dir():
        print(f"[error] no recordings at {src_dir}", file=sys.stderr)
        return 1

    out_dir = DATASET_DIR / speaker
    wavs_dir = out_dir / "wavs"
    wavs_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    durations = []
    skipped = 0

    src_files = sorted(src_dir.glob("*.wav"))
    print(f"processing {len(src_files)} recordings for {speaker} → {out_dir}")

    for wav_in in src_files:
        sentence_id = wav_in.stem
        if sentence_id not in sentences:
            print(f"  skip (not in script): {sentence_id}")
            skipped += 1
            continue
        wav_out = wavs_dir / f"{sentence_id}.wav"
        duration = process_one(wav_in, wav_out)
        durations.append(duration)
        rows.append({
            "audio_file": str(wav_out.absolute()),
            "text": sentences[sentence_id]["text"],
        })

    metadata = out_dir / "metadata.csv"
    with metadata.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="|", quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["audio_file", "text"])
        for row in rows:
            writer.writerow([row["audio_file"], row["text"]])

    total = sum(durations)
    print()
    print(f"wrote {len(rows)} WAVs to {wavs_dir} (skipped {skipped})")
    print(f"metadata: {metadata}")
    print(f"total audio: {total:.1f}s = {total/60:.1f} min")
    print(f"sample rate: {TARGET_SR} Hz, mono, PCM_16, peak-normalized to {PEAK_TARGET}")
    print()
    print("next step — build the Arrow dataset F5-TTS' trainer expects:")
    print(f"  uv run python -m f5_tts.train.datasets.prepare_csv_wavs \\")
    print(f"      {metadata} \\")
    print(f"      data/dataset/{speaker}_pinyin")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("speaker", help="speaker id (e.g. sonali)")
    args = p.parse_args()
    sys.exit(main(args.speaker))
