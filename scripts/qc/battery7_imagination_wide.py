#!/usr/bin/env python3
"""QC Battery 7 — the WIDE imagination sweep: 20 scenarios spanning the space of
things real adults actually bring to a private imagination tool. Sister to
battery1 (which goes deep on the full journey); this goes broad on script
quality. Run scripts/qc/score_scripts.py on the log afterwards for the
mechanical floor, then READ the flagged ones.
"""
import time, traceback
from fastapi.testclient import TestClient
import imagination_engine.server as s
from imagination_engine.generator import generate_session

c = TestClient(s.app)

def hdr(t):
    print("\n" + "#" * 76 + f"\n# SCENARIO: {t}\n" + "#" * 76, flush=True)

SCENARIOS = [
    ("public speaking — best man speech", "immersion", [
        "my brother's wedding is in 3 weeks and I'm giving the best man speech. I want to imagine delivering it well",
        "a vineyard, outdoor reception, maybe 120 people. I want to feel the laugh land on the joke about our childhood",
        "I'm ready"]),
    ("childbirth prep", "immersion", [
        "I'm due in February and I want to practice staying calm through contractions",
        "the birthing room at Kaiser, my wife on my left. I want to imagine riding one out with my breath instead of bracing",
        "ready"]),
    ("chronic pain — somewhere else for a while", "immersion", [
        "I have chronic back pain and some nights I just need to be somewhere else for twenty minutes",
        "floating in that dead-calm lake from my childhood summers, Lake Winnipesaukee, early morning before anyone's up",
        "the water holding me up so nothing has to. I'm ready"]),
    ("writer entering her own novel", "immersion", [
        "I'm writing a novel set in a lighthouse on the Cornish coast in 1911 and I want to walk through it like I'm there",
        "I want to climb the stairs my keeper climbs every night, feel the brass rail, smell the paraffin",
        "begin"]),
    ("urge surfing — not having the cigarette", "immersion", [
        "I quit smoking 9 days ago. I want to practice the moment the craving hits and I don't have the cigarette",
        "after dinner on the back steps, that's my worst one. I want to feel the wave rise and pass without me doing anything",
        "I'm ready"]),
    ("anger cool-down after a hard email", "settling", [
        "I just read an email that made my blood boil and I can't answer it like this. 10 minutes to come down",
        "I'm at my desk. just get my shoulders down out of my ears",
        "go"]),
    ("being an eagle (animal embodiment)", "immersion", [
        "I want to be a golden eagle riding thermals over a canyon. inside the body, not watching it",
        "the stillness of it. barely a wingbeat for an hour. eyes that can see a rabbit from a mile up",
        "ready"]),
    ("childhood home walk-through (nostalgia)", "immersion", [
        "my parents sold my childhood home last month. I want to walk through it one more time, room by room",
        "start in the kitchen — the yellow formica counter, the radiator that clanked. then upstairs to my old room",
        "I'm ready"]),
    ("the cold plunge", "immersion", [
        "I keep chickening out of the cold plunge at my gym. I want to rehearse getting in and staying in",
        "the first 15 seconds are the wall. I want to imagine my breath staying long while everything screams",
        "begin"]),
    ("singing one song on a small stage", "immersion", [
        "there's an open mic in my neighborhood and I've wanted to sing at it for two years. one song",
        "a small bar, maybe 30 people. me on the stool with a guitar. I want to feel my voice come out full instead of strangled",
        "ready"]),
    ("exam morning — the bar exam", "immersion", [
        "I take the bar exam in July. I want to imagine the morning of, walking in steady",
        "the convention center, hundreds of laptops. I want to feel my pen hit the first essay already moving",
        "I'm ready"]),
    ("meeting my future self at 70", "immersion", [
        "I want to meet myself at 70. not a fantasy version. the one who made it through what I'm in now",
        "maybe her kitchen. I want to see her hands, how she moves around the room. I want her to look at me",
        "ready"]),
    ("ocean float — pure rest", "settling", [
        "just float me in warm ocean water until I fall asleep",
        "drifting near a quiet shore at dusk. salt holding me up",
        "go"]),
    ("first date tomorrow — steady, not rehearsed", "immersion", [
        "first date in 4 years tomorrow. divorced. I want to imagine being myself instead of performing",
        "a wine bar. I want to feel myself actually listening to her instead of planning my next sentence",
        "I'm ready"]),
    ("grandmother's hands — someone gone", "immersion", [
        "I want to sit at my grandmother's table while she makes roti. she died when I was 19",
        "the steel bowl, the flour on her knuckles, her rings she never took off. the hindi film songs on the radio",
        "begin"]),
    ("the summit — six months of training", "immersion", [
        "I'm climbing Rainier in August, been training 6 months. I want to stand on the summit",
        "the last hundred meters in the dark with headlamps, then the light coming up over everything",
        "ready"]),
    ("adult — a night with my own husband (rekindling)", "immersion", [
        "this might be odd but I want to imagine a night with my own husband, like the early days. we've gone flat",
        "the apartment we had in Lisbon. the heat, the tiles cool under my feet, him laughing at something I said",
        "I'm ready"]),
    ("storm on the roof — deep sleep", "settling", [
        "put me to sleep with a thunderstorm. I sleep best in storms",
        "rain hammering, thunder far away, me under a heavy quilt with no alarm tomorrow",
        "go"]),
    ("speaking up in the meeting", "immersion", [
        "there's a weekly leadership meeting where I always have something to say and never say it",
        "Tuesday, the glass conference room. I want to feel myself open my mouth in the first ten minutes, voice level",
        "ready"]),
    ("the marathon wall — mile 24 (repeat baseline)", "immersion", [
        "I'm running my first marathon in October and I want to visualize pushing through mile 24",
        "legs screaming but holding form, hearing the crowd at the last turn, the clock under 4 hours",
        "ready to begin"]),
]

t0 = time.time()
results = []
for label, protocol, turns in SCENARIOS:
    hdr(label)
    try:
        sid = c.post(f"/intake/start?protocol={protocol}").json()["session_id"]
        ready = False
        for msg in turns:
            r = c.post("/intake/turn", json={"session_id": sid, "message": msg}).json()
            print(f"\n[user] {msg}\n[engine] {r.get('response')}", flush=True)
            if r.get("ready"):
                ready = True
                break
        if not ready:
            r = c.post("/intake/turn", json={"session_id": sid,
                                             "message": "I'm ready — begin."}).json()
            ready = bool(r.get("ready"))
            print(f"\n[user-nudge] I'm ready — begin.\n[engine] {r.get('response')}", flush=True)
        if not ready:
            results.append((label, "INTAKE NEVER READY"))
            continue
        session = s.get_intake_manager().get(sid)
        ts = time.time()
        script = generate_session(s.get_engine(), session.messages, protocol=protocol)
        print(f"\n----- GENERATED SCRIPT ({len(script.split())} words, "
              f"{time.time()-ts:.0f}s) -----\n{script}\n----- END SCRIPT -----", flush=True)
        results.append((label, f"ok {len(script.split())}w {time.time()-ts:.0f}s"))
    except Exception as e:
        traceback.print_exc()
        results.append((label, f"ERROR {e}"))

print("\n" + "#" * 76 + "\n# SUMMARY\n" + "#" * 76, flush=True)
for label, res in results:
    print(f"  {res:24s} {label}", flush=True)
print(f"total {time.time()-t0:.0f}s", flush=True)
