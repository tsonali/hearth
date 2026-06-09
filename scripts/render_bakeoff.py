#!/usr/bin/env python3
"""Render the SAME guided passage in each voice, so Sonali can judge by ear.
Voices: Chatterbox 'her' + 'him' (MIT system voices) and the F5 'sonali' clone.
Outputs to ~/Downloads/hearth-voice-bakeoff/."""
import os, sys, traceback
OUT = os.path.expanduser("~/Downloads/hearth-voice-bakeoff")
os.makedirs(OUT, exist_ok=True)

# a concrete, slow, settling passage (the kind the product actually delivers)
PASSAGE = (
    "Let your eyes close. For the next little while there is nowhere you have to be. "
    "Feel the weight of your body where it rests — the chair, or the bed, holding you. "
    "Notice your breath, already moving, without your help. "
    "Now picture a window, rain running down the glass in slow, wandering lines. "
    "The room is warm. A cup sits beside you, and the heat of it reaches your hands. "
    "Outside, the rain keeps its soft, uneven rhythm against the pane. "
    "There is nothing to fix here. Just the warmth, the glass, the rain, and your breath."
)

def save(name, wav_bytes):
    p = os.path.join(OUT, name + ".wav")
    with open(p, "wb") as f: f.write(wav_bytes)
    print(f"  saved {p} ({len(wav_bytes)//1000} KB)", flush=True)

def render(label, loader):
    print(f"\n=== {label} ===", flush=True)
    try:
        v = loader()
        save(label, v.speak(PASSAGE))
    except Exception as e:
        print(f"  FAILED: {e}", flush=True)
        traceback.print_exc()

if __name__ == "__main__":
    from imagination_engine.tts import make_voice, F5Voice
    render("her_chatterbox", lambda: make_voice("her"))
    render("him_chatterbox", lambda: make_voice("him"))
    render("sonali_f5",      lambda: F5Voice.load())
    print(f"\ndone — open {OUT} and listen. Same words, three voices.", flush=True)
