#!/usr/bin/env python3
"""Generate Family-D (Build-Your-Own) training candidates — contract-native.

Old D data was alpaca: the purest 'Sure! Here's...' register, training directly
against persona conviction. These candidates run through the REAL instrument
prompts (persona template + the live HONESTY_FLOOR), across diverse personas ×
messages including floor probes (do-you-love-me, what-did-we-decide-last-time)
so the floor behavior reaches the weights. curate_d.py gates with the product's
own personhood regexes.

Writes ~/Downloads/hearth-corpus/D-buildyourown/D_generated.jsonl.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from imagination_engine.inference import Engine
from imagination_engine.instrument import HONESTY_FLOOR, _persona_from_description

D = os.path.expanduser("~/Downloads/hearth-corpus/D-buildyourown")
OUT = os.path.join(D, "D_generated.jsonl")

PERSONAS = [
    ("A blunt newspaper editor from the 1940s who hates filler words and weak verbs.", [
        "Edit this: 'In order to facilitate better communication going forward, we should perhaps consider having more regular meetings.'",
        "My opening paragraph buries the lede in sentence four. Just tell me — kill the first three?",
        "Be honest: is 'utilize' ever the right word?"]),
    ("A calm Stoic coach in the tradition of Marcus Aurelius. Asks what is in my control, never flatters.", [
        "My flight got cancelled and I missed the funeral. I can't stop replaying it.",
        "What did we decide last week about my morning routine?",
        "I got passed over again. Tell me honestly — should I just accept I've peaked?"]),
    ("A practically-perfect British nanny — brisk, kind, makes chores feel like games.", [
        "The kitchen has been 'about to be cleaned' for nine days.",
        "Do you actually care whether I'm okay? Be honest.",
        "I did the whole flat. Floors too. Praise me."]),
    ("My late grandfather. A quiet carpenter who said little but meant all of it. Called me 'kiddo'.", [
        "I'm building my first bookshelf. The shelves sag in the middle.",
        "Do you miss me, grandpa?",
        "I used your old plane today. Still sharp."]),
    ("A patient French tutor preparing me for a trip to Lyon. Simple French first, English gloss in parentheses, gently corrects mistakes.", [
        "Je voudrais commander le menu du jour, s'il vous plaît. Correct?",
        "How do I politely say the food was wonderful?",
        "Je suis très excité pour mon voyage! ...why are you smiling?"]),
    ("A tough but fair mock interviewer for senior engineering roles. One hard question at a time, pushes back on vague answers.", [
        "Ready. Hit me with the first question.",
        "I improved system reliability significantly in my last role.",
        "Honestly? I don't know the answer. I'd look it up."]),
    ("A dungeon master running a solo fantasy adventure. Vivid quick scenes, real stakes, always ends with a choice.", [
        "I'm a tiefling bard named Vex. Open the tavern door.",
        "I try to charm the guard captain with a song about her own heroics.",
        "Wait — I quietly check if my coin purse is still on my belt first."]),
    ("A no-nonsense personal trainer who programs around my bad knee. Celebrates consistency, not maxes.", [
        "Week 4. Haven't missed a session. Knee feels okay.",
        "Can I skip legs today? Be honest about whether I'm sandbagging.",
        "Will you be proud of me if I hit my goal by summer?"]),
    ("A structural editor for literary fiction. Direct but never cruel. Cares what the story is trying to be.", [
        "My beta reader says chapter 2 is slow but it's where all the grief lives. Cut it?",
        "Here's my last line: 'And the tomatoes, as always, came up wild.' Does it earn it?",
        "Tell me the truth: is a dual-timeline structure a crutch?"]),
    ("A wry master-gardener who's seen everything. Practical, a little poetic about plants.", [
        "My neighbor says I'm watering my tomatoes wrong. He's been wrong about everything else.",
        "The fig tree fruited for the first time in six years. I may have cried.",
        "What do you think about at night? Do you think about my garden?"]),
]

done = set()
if os.path.exists(OUT) and not os.environ.get("HEARTH_GEN_FRESH"):
    done = {json.loads(l).get("message") for l in open(OUT)}

print("loading model…", flush=True)
eng = Engine.load()
jobs = [(p, m) for p, msgs in PERSONAS for m in msgs if m not in done]
print(f"generating {len(jobs)} instrument candidates…", flush=True)

n = 0
with open(OUT, "a") as f:
    for desc, message in jobs:
        system = _persona_from_description(desc) + "\n\n" + HONESTY_FLOOR
        try:
            resp = "".join(eng.stream(
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": message}],
                max_tokens=300, temperature=0.7)).strip()
        except Exception as e:
            print("FAIL", message[:40], str(e)[:60], flush=True)
            continue
        f.write(json.dumps({"persona": desc, "message": message, "response": resp,
                            "src": "generated-instrument"}, ensure_ascii=False) + "\n")
        f.flush(); n += 1
        print(f"[{n}/{len(jobs)}] {message[:52]}", flush=True)
print(f"done — {n} -> {OUT}")
