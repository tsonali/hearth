"""Inspect a speaker's recorded WAV files and report issues.

Usage:
    uv run python scripts/inspect_recordings.py <speaker_id>

Checks:
- Which sentence IDs are recorded, missing, or extra (not in the script).
- Sample rate, channels, duration of each file.
- Peak / RMS amplitude — flags silent, clipping, or very quiet files.
- Per-register summary (Harvard / general / guided-imagery).
- Outliers worth a second listen.
"""

from __future__ import annotations

import json
import math
import statistics
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RECORDING_SCRIPT = PROJECT_ROOT / "data" / "recording-script.json"
RECORDINGS_DIR = PROJECT_ROOT / "data" / "recordings"


def db(x: float) -> float:
    """Linear amplitude → dBFS (0 dBFS = full scale)."""
    if x <= 0:
        return -math.inf
    return 20.0 * math.log10(x)


def inspect(speaker_id: str) -> int:
    speaker_dir = RECORDINGS_DIR / speaker_id
    if not speaker_dir.is_dir():
        print(f"[error] no recordings directory at {speaker_dir}")
        return 1

    script = json.loads(RECORDING_SCRIPT.read_text())
    expected = {s["id"]: s for s in script["sentences"]}

    wavs = sorted(speaker_dir.glob("*.wav"))
    found_ids = {p.stem for p in wavs}
    missing = sorted(set(expected) - found_ids)
    extra = sorted(found_ids - set(expected))

    print(f"speaker:           {speaker_id}")
    print(f"directory:         {speaker_dir.relative_to(PROJECT_ROOT)}")
    print(f"sentences in script: {len(expected)}")
    print(f"recorded:          {len(wavs)} ({100*len(wavs)/len(expected):.0f}%)")
    print(f"missing:           {len(missing)}")
    print(f"extra (not in script): {len(extra)}")
    if extra:
        print(f"  extras: {extra}")

    # Per-file stats.
    rows = []
    for p in wavs:
        try:
            data, sr = sf.read(str(p), dtype="float32")
        except Exception as e:
            print(f"[unreadable] {p.name}: {e}")
            continue
        if data.ndim == 2:
            data = data.mean(axis=1)  # downmix any accidental stereo
        peak = float(np.max(np.abs(data))) if len(data) else 0.0
        rms = float(np.sqrt(np.mean(data**2))) if len(data) else 0.0
        duration = len(data) / sr if sr else 0.0
        register = expected[p.stem]["register"] if p.stem in expected else "?"
        rows.append({
            "id": p.stem,
            "register": register,
            "sr": sr,
            "channels": 1,
            "duration": duration,
            "peak": peak,
            "rms": rms,
            "size_kb": p.stat().st_size / 1024,
        })

    if not rows:
        print("[error] no readable WAVs")
        return 1

    # Aggregate stats.
    durations = [r["duration"] for r in rows]
    peaks = [r["peak"] for r in rows]
    rmses = [r["rms"] for r in rows]
    srs = sorted({r["sr"] for r in rows})

    print()
    print(f"sample rates seen: {srs} Hz  {'(CONSISTENT)' if len(srs) == 1 else '(INCONSISTENT — flag)'}")
    print(f"total audio:       {sum(durations):.1f} s = {sum(durations)/60:.1f} min")
    print(f"total disk:        {sum(r['size_kb'] for r in rows)/1024:.1f} MB")
    print()
    print("duration (sec):")
    print(f"  min  / mean / max:  {min(durations):.2f} / {statistics.mean(durations):.2f} / {max(durations):.2f}")
    print(f"  median:             {statistics.median(durations):.2f}")
    print()
    print("peak amplitude (dBFS — 0 is loudest possible, -3 is healthy headroom):")
    print(f"  min  / mean / max:  {db(min(peaks)):.1f} / {statistics.mean([db(p) for p in peaks if p>0]):.1f} / {db(max(peaks)):.1f}")
    print()
    print("RMS (loudness — broadcast voice is typically -23 to -16 dBFS):")
    valid_rmses = [db(r) for r in rmses if r > 0]
    print(f"  min  / mean / max:  {min(valid_rmses):.1f} / {statistics.mean(valid_rmses):.1f} / {max(valid_rmses):.1f}")

    # Per-register summary.
    print()
    print("per-register:")
    for reg in ("balanced", "general", "guided"):
        sub = [r for r in rows if r["register"] == reg]
        if not sub:
            continue
        n = len(sub)
        expected_n = sum(1 for s in expected.values() if s["register"] == reg)
        avg_dur = statistics.mean(r["duration"] for r in sub)
        print(f"  {reg:9s}: {n}/{expected_n}  avg {avg_dur:.2f}s  total {sum(r['duration'] for r in sub)/60:.1f}min")

    # Outliers.
    print()
    print("outliers worth a re-listen:")
    flagged = 0

    # Very short — likely cut off or just silence
    too_short = [r for r in rows if r["duration"] < 0.6]
    if too_short:
        flagged += len(too_short)
        print(f"  too short (<0.6s):    {len(too_short)}: {', '.join(r['id'] for r in too_short[:8])}{'…' if len(too_short)>8 else ''}")

    # Very long for the text
    too_long = [r for r in rows if r["duration"] > 18.0]
    if too_long:
        flagged += len(too_long)
        print(f"  too long (>18s):     {len(too_long)}: {', '.join(r['id'] for r in too_long[:8])}{'…' if len(too_long)>8 else ''}")

    # Clipping
    clipping = [r for r in rows if r["peak"] >= 0.999]
    if clipping:
        flagged += len(clipping)
        print(f"  clipping (peak=1.0):  {len(clipping)}: {', '.join(r['id'] for r in clipping[:8])}{'…' if len(clipping)>8 else ''}")

    # Very quiet
    too_quiet = [r for r in rows if r["rms"] > 0 and db(r["rms"]) < -45]
    if too_quiet:
        flagged += len(too_quiet)
        print(f"  very quiet (<-45dB):  {len(too_quiet)}: {', '.join(r['id'] for r in too_quiet[:8])}{'…' if len(too_quiet)>8 else ''}")

    # Silent
    silent = [r for r in rows if r["peak"] < 0.001]
    if silent:
        flagged += len(silent)
        print(f"  silent:               {len(silent)}: {', '.join(r['id'] for r in silent[:8])}{'…' if len(silent)>8 else ''}")

    if not flagged:
        print("  (none — clean dataset)")

    if missing:
        print()
        print(f"missing sentence IDs ({len(missing)}):")
        for i in range(0, len(missing), 12):
            print("  " + " ".join(missing[i:i+12]))

    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: uv run python scripts/inspect_recordings.py <speaker_id>")
        sys.exit(2)
    sys.exit(inspect(sys.argv[1]))
