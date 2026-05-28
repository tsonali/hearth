# System voices — reference clips

These two WAV files are the reference clips Chatterbox uses to clone the two
curated **system voices** that appear in the intake voice picker (`her` and
`him`). They are NOT the user's own voice — that lives in `data/dataset/` and
goes through F5-TTS fine-tuning.

```
data/system_voices/
├── her.wav   ← 10–15 second clean clip of "a warm, unhurried woman"
└── him.wav   ← 10–15 second clean clip of "a slow, measured man"
```

## What makes a good reference clip

- **Length:** 10–15 seconds. Chatterbox needs enough to lock the voice
  character but extra audio doesn't help.
- **Content:** Slow descriptive prose, not dialogue. Audiobook narration is
  ideal. NOT punchy, NOT performative — calm, intimate, audiobook-narrator.
- **Quality:** Clean mono, no background noise, no music, no breath bursts.
  44.1 kHz or 24 kHz, 16-bit or float32.
- **One sentence's worth of speech.** A natural-paced sentence and a half
  at most. Chatterbox dislikes truncated phrases.

## Where to source (mid-2026 best picks)

Both candidates are **public domain** via LibriVox:

### `her.wav` — Elizabeth Klett reading *Jane Eyre*
- LibriVox page: https://librivox.org/jane-eyre-by-charlotte-bronte/
- Recommended chapter: 1 or 2. Find a long descriptive passage; trim to
  ~12 seconds.
- Why: One of LibriVox's strongest narrators. Warm British, intimate
  audiobook delivery. Exactly the "sexy relaxed" target.

### `him.wav` — Mark F. Smith reading *The Call of the Wild*
- LibriVox page: https://librivox.org/the-call-of-the-wild-by-jack-london/
- Recommended chapter: 1. Find a slow descriptive sentence; trim to ~12 s.
- Why: Dry, measured, low. Audiobook-natural pacing.

## How to make the clips

Manual (recommended for first pass — you can listen as you trim):

1. Download the LibriVox MP3 of the chapter you picked.
2. Open in Audacity, GarageBand, or any DAW.
3. Find a clean 10–15s passage of slow prose. Trim to it.
4. Export as mono WAV, 24 kHz, 16-bit PCM.
5. Save as `data/system_voices/her.wav` (or `him.wav`).

Programmatic alternative — `scripts/download_system_voices.py` takes a URL +
start time + duration and produces the trimmed WAV. Update the URLs at the
top of that script with your chosen LibriVox chapter links.

## Privacy / gitignore

These files are **not** committed to git. They are derived artifacts (you
could regenerate them from a public source). Keeping them out of the repo
also means the repo stays small and we don't accidentally publish
impersonation-risk audio of any specific narrator.

See `.gitignore` — `data/system_voices/*.wav` is excluded.
