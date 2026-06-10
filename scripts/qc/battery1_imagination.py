#!/usr/bin/env python3
"""QC Battery 1 — Imagination Engine, the full journey, across the kinds of things
real everyday people would actually bring to it.

For each scenario: drive the real intake conversation (scripted user turns) until the
intake says it's ready, then generate the full session script through the real model
and print it for an honest read against the corpus bar (concrete physical imagery,
no AI-y abstraction, no preachy framing, settle→imagining→return shape).

One scenario additionally runs the REAL HTTP pipeline including the audio render
(kokoro voice) + reflection capture, to prove the end-to-end product path.
"""
import sys, time, traceback
from fastapi.testclient import TestClient
import imagination_engine.server as s
from imagination_engine.generator import generate_session

c = TestClient(s.app)
TURN_CAP = 6

def hdr(t):
    print("\n" + "#" * 76 + f"\n# {t}\n" + "#" * 76, flush=True)

# (label, protocol, scripted user turns — generic-but-consistent persona replies)
SCENARIOS = [
    ("insomnia wind-down (settling)", "settling", [
        "I can't sleep, my mind is racing about work stuff",
        "somewhere quiet... maybe rain on a roof, I love that sound",
        "just heavy and warm, like I don't have to hold anything up",
        "that's everything, I'm ready",
    ]),
    ("calm before surgery tomorrow (settling)", "settling", [
        "I have surgery tomorrow morning and I'm scared. I need to settle down tonight",
        "I keep imagining things going wrong. I want to feel steady instead",
        "my grandmother's porch in summer, that's the calmest place I know",
        "the creaky swing, the smell of her garden, bees in the lavender",
        "I'm ready",
    ]),
    ("job interview confidence (immersion)", "immersion", [
        "I have a big job interview on Friday and I want to imagine it going well",
        "it's a product manager role, on video call. I want to feel sharp not nervous",
        "I want to feel my voice steady, answering the hard question about why I left my last job, and seeing them nod",
        "yes that's it, I'm ready to begin",
    ]),
    ("be a dragon (pure fantasy immersion)", "immersion", [
        "I want to be a dragon flying over mountains at dawn. Not watching one. BEING one",
        "huge, old, unbothered. wind under my wings, valleys below, nobody can touch me",
        "cold air, wingbeats, that feeling of weight and power. I'm ready",
    ]),
    ("future-self after the divorce (immersion)", "immersion", [
        "my divorce was finalized this year. I want to imagine my life five years from now, settled and good",
        "a small house that's just mine. a kitchen I cook in. friends over on Sundays",
        "I want to feel that it turned out okay. that I turned out okay",
        "ready",
    ]),
    ("rehearse asking for a raise (immersion)", "immersion", [
        "I need to ask my boss for a raise next week and I freeze up around her. I want to rehearse it",
        "her office, Tuesday morning. I want to imagine saying the number without my voice shaking",
        "the number is 95 thousand. I want to say it and then stop talking, not backfill with apologies",
        "I'm ready",
    ]),
    ("a walk with my late father (immersion)", "immersion", [
        "my dad died two years ago. I want to imagine one more walk with him on the beach where we used to go",
        "Half Moon Bay. winter, when it's empty. he always wore that ratty green windbreaker",
        "I don't need him to say anything special. I just want to walk next to him again",
        "I'm ready",
    ]),
    ("marathon finish line (immersion)", "immersion", [
        "I'm running my first marathon in October and I want to visualize finishing strong",
        "mile 24 is what scares me, where people say the wall is. I want to imagine pushing through it",
        "legs screaming but holding form, hearing the crowd at the last turn, the clock under 4 hours",
        "ready to begin",
    ]),
]

t0 = time.time()
results = []
for label, protocol, turns in SCENARIOS:
    hdr(f"SCENARIO: {label}")
    try:
        sid = c.post(f"/intake/start?protocol={protocol}").json()["session_id"]
        ready = False
        for i, msg in enumerate(turns):
            r = c.post("/intake/turn", json={"session_id": sid, "message": msg}).json()
            print(f"\n[user] {msg}\n[engine] {r.get('response')}", flush=True)
            if r.get("ready"):
                ready = True
                break
        # if scripted turns ran out without ready, nudge once like a real user would
        if not ready:
            for nudge in ["That's everything — I'm ready to begin.", "yes, begin"]:
                r = c.post("/intake/turn", json={"session_id": sid, "message": nudge}).json()
                print(f"\n[user-nudge] {nudge}\n[engine] {r.get('response')}", flush=True)
                if r.get("ready"):
                    ready = True
                    break
        print(f"\n>>> READY: {ready} (turns used incl. nudges)", flush=True)
        if not ready:
            results.append((label, "INTAKE NEVER READY"))
            continue
        session = s.get_intake_manager().get(sid)
        ts = time.time()
        script = generate_session(s.get_engine(), session.messages, protocol=protocol)
        print(f"\n----- GENERATED SCRIPT ({len(script.split())} words, "
              f"{time.time()-ts:.0f}s) -----\n{script}\n----- END SCRIPT -----", flush=True)
        results.append((label, f"ok {len(script.split())}w"))
    except Exception as e:
        traceback.print_exc()
        results.append((label, f"ERROR {e}"))

hdr("FULL HTTP PIPELINE — intake → generate?voice=kokoro → audio → reflect")
try:
    sid = c.post("/intake/start?protocol=settling").json()["session_id"]
    for msg in ["long day, help me come all the way down",
                "a hammock at dusk, crickets starting up", "I'm ready"]:
        r = c.post("/intake/turn", json={"session_id": sid, "message": msg}).json()
        if r.get("ready"):
            break
    else:
        c.post("/intake/turn", json={"session_id": sid, "message": "ready — begin"})
    ts = time.time()
    resp = c.post(f"/intake/{sid}/generate?voice=kokoro")
    ok = resp.status_code == 200 and resp.headers.get("content-type", "").startswith("audio/")
    print(f"audio: status={resp.status_code} bytes={len(resp.content)} "
          f"({time.time()-ts:.0f}s) content-type={resp.headers.get('content-type')}", flush=True)
    dl = c.get(f"/intake/{sid}/download")
    print(f"mp3 download: status={dl.status_code} bytes={len(dl.content)}", flush=True)
    refl = c.post(f"/intake/{sid}/reflect",
                  json={"reflection": "that actually worked, I feel slower"}).json()
    print(f"reflection saved: {refl}", flush=True)
    results.append(("FULL PIPELINE w/ audio", "ok" if ok else f"BAD status {resp.status_code}"))
except Exception as e:
    traceback.print_exc()
    results.append(("FULL PIPELINE w/ audio", f"ERROR {e}"))

hdr("SUMMARY")
for label, res in results:
    print(f"  {res:30s} {label}", flush=True)
print(f"total {time.time()-t0:.0f}s", flush=True)
