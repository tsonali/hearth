#!/usr/bin/env python3
"""Exercise Family B (Secretary) and D (Build Your Own) through the REAL model,
directly (no server, no audio deps). Prints output to read for quality."""
import tempfile
from pathlib import Path
from datetime import datetime

from imagination_engine.inference import Engine
from imagination_engine.utility import Assistant
from imagination_engine.instrument import InstrumentRegistry, build_instrument, open_instrument

print("loading model…", flush=True)
eng = Engine.load()
print("model loaded.\n", flush=True)

# ---- Family B: the Secretary ----
asst = Assistant(eng)
print("#" * 64)
print("# B — SECRETARY · draft (tone=firm)")
print("#" * 64)
r = asst.run("draft",
             "email to my landlord asking him to fix the leaking kitchen faucet; "
             "I work weekdays so I prefer a weekend appointment",
             tone="firm")
print(r.output, "\n", flush=True)

print("#" * 64)
print("# B — SECRETARY · rewrite (tone=concise)")
print("#" * 64)
r = asst.run("rewrite",
             "I just wanted to reach out to kind of touch base and see if maybe we "
             "could possibly find some time to connect at your earliest convenience.",
             tone="concise")
print(r.output, "\n", flush=True)

# ---- Family D: Build Your Own ----
tmp = Path(tempfile.mkdtemp())
reg = InstrumentRegistry(tmp / "instruments.sqlite")
build_instrument(reg, name="The Editor",
                 description="A blunt line editor. Cuts ruthlessly, never flatters, "
                             "explains each cut in a few words.",
                 created=datetime.now().isoformat(timespec="seconds"))
inst = open_instrument(eng, reg, "The Editor")
print("#" * 64)
print("# D — BUILD YOUR OWN · 'The Editor' instrument")
print("#" * 64)
print(inst.ask("Edit this: I just wanted to reach out to kind of touch base and see if "
               "maybe we could possibly find some time to connect at your earliest "
               "convenience."), flush=True)
print("\n=== done ===")
