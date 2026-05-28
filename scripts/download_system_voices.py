"""Download + trim LibriVox audio into Chatterbox reference clips.

Sources a chapter MP3 from archive.org's LibriVox catalog, trims a clean
10-15s window, resamples to mono 24 kHz, and writes the WAV to
`data/system_voices/{name}.wav`.

The defaults pre-populate the two voices the founder picked: Elizabeth
Klett's *Jane Eyre* for `her`, Mark F. Smith's *Call of the Wild* for `him`.
You can override any source via CLI flags.

Usage
-----
    # Download both defaults:
    .venv/bin/python scripts/download_system_voices.py

    # Or one at a time, with explicit timestamps:
    .venv/bin/python scripts/download_system_voices.py --only her \\
        --her-url https://www.archive.org/download/.../jane_eyre_01.mp3 \\
        --her-start 42.0 --her-duration 13.0

After downloading, listen to the resulting WAVs. Chatterbox's output voice
character is dominated by these clips — if either doesn't sound like the
intimate audiobook quality you want, pick a different window and re-run.
"""

from __future__ import annotations

import argparse
import io
import sys
import urllib.request
from pathlib import Path


# ---------------------------------------------------------------------------
# Defaults.
#
# IMPORTANT: archive.org chapter URLs change format over time and there is
# more than one valid recording per book on LibriVox. Before relying on these
# defaults, browse the LibriVox pages linked in
# data/system_voices/README.md and confirm the recording is still the one
# you want. The trim windows below are conservative middles-of-chapters.
# ---------------------------------------------------------------------------

DEFAULT_HER_URL = (
    # Jane Eyre, Chapter 1 — the canonical jane_eyre_librivox item on
    # archive.org (the earliest/most-popular LibriVox edition; widely
    # attributed to Elizabeth Klett). Verified live 2026-05-28.
    "https://archive.org/download/jane_eyre_librivox/jane_eyre_01_bronte_64kb.mp3"
)
DEFAULT_HER_START = 110.0      # seconds into the chapter — skip LibriVox intro
DEFAULT_HER_DURATION = 13.0    # seconds of clip

DEFAULT_HIM_URL = (
    # Call of the Wild, Chapter 1 — the canonical call_of_the_wild item
    # on archive.org (earliest/most-popular LibriVox edition; widely
    # attributed to Mark F. Smith). Verified live 2026-05-28.
    "https://archive.org/download/call_of_the_wild/call_of_the_wild_1_london_64kb.mp3"
)
DEFAULT_HIM_START = 95.0       # seconds in — skip LibriVox intro
DEFAULT_HIM_DURATION = 13.0


# Output spec: mono 24 kHz, 16-bit PCM.
OUTPUT_SAMPLE_RATE = 24000


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = PROJECT_ROOT / "data" / "system_voices"


def download_and_trim(url: str, start_s: float, duration_s: float, out_path: Path) -> None:
    """Download the MP3 at `url`, trim to the window, write WAV to `out_path`.

    Uses librosa for resampling (already a Chatterbox dependency, so no
    extra install). Doesn't shell out to ffmpeg — keeps this script
    self-contained for non-technical users.
    """
    print(f"  ↓ downloading {url}")
    with urllib.request.urlopen(url) as resp:
        mp3_bytes = resp.read()
    print(f"    {len(mp3_bytes) / (1024 * 1024):.1f} MB")

    # Lazy imports — script can still --help without these installed.
    import librosa
    import soundfile as sf

    audio, sr = librosa.load(
        io.BytesIO(mp3_bytes),
        sr=OUTPUT_SAMPLE_RATE,
        mono=True,
        offset=start_s,
        duration=duration_s,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(out_path, audio, OUTPUT_SAMPLE_RATE, subtype="PCM_16")
    print(f"  ✓ wrote {out_path} ({len(audio) / OUTPUT_SAMPLE_RATE:.1f}s)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--only", choices=["her", "him"], help="download just one voice")
    ap.add_argument("--her-url", default=DEFAULT_HER_URL)
    ap.add_argument("--her-start", type=float, default=DEFAULT_HER_START)
    ap.add_argument("--her-duration", type=float, default=DEFAULT_HER_DURATION)
    ap.add_argument("--him-url", default=DEFAULT_HIM_URL)
    ap.add_argument("--him-start", type=float, default=DEFAULT_HIM_START)
    ap.add_argument("--him-duration", type=float, default=DEFAULT_HIM_DURATION)
    args = ap.parse_args()

    targets = []
    if args.only in (None, "her"):
        targets.append(("her", args.her_url, args.her_start, args.her_duration))
    if args.only in (None, "him"):
        targets.append(("him", args.him_url, args.him_start, args.him_duration))

    for name, url, start, dur in targets:
        out = OUT_DIR / f"{name}.wav"
        print(f"\n[{name}]")
        try:
            download_and_trim(url, start, dur, out)
        except Exception as e:
            print(f"  ✗ failed: {e}", file=sys.stderr)
            print(f"    Try a different archive.org URL — see "
                  f"data/system_voices/README.md.", file=sys.stderr)
            sys.exit(1)

    print("\nDone. Listen to the clips before using them — Chatterbox's "
          "output voice character is dominated by these.")


if __name__ == "__main__":
    main()
