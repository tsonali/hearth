#!/usr/bin/env python3
"""Generate Family-A candidate scripts, few-shot-anchored on the real GOLD exemplars.

The proven lever (ab_fewshot_test): showing the model real, concrete human scripts
pulls its output toward the physical-specific and away from the AI-y abstract. This
runs that at volume across diverse intakes (both protocols), so we get a pile of
decent candidates to score + curate back into silver/gold. Output is then fed to
score_a_quality.py — only the concrete ones survive.

Runs on the mini (loads Qwen). Writes A_generated.jsonl into the private corpus.
"""
import json, os, re
from imagination_engine.inference import Engine

ROOT = os.path.expanduser("~/Downloads/hearth-corpus")
A = os.path.join(ROOT, "A-imagination")
GOLD = os.path.join(A, "A_gold.jsonl")
OUT = os.path.join(A, "A_generated.jsonl")

# CLEAN few-shot anchors — strip the provenance/frontmatter that was leaking into the
# va-001 text (Sonali caught it: "title:/author_credit:" would teach the model garbage).
import re as _re
def _clean_anchor(t):
    keep = []
    for ln in t.splitlines():
        s = ln.strip()
        if _re.match(r'^(title|author_credit|protocol|concrete_nouns_test|status|intake|'
                     r'words|license|source|url|caveat|note)\s*:', s, _re.I):
            continue
        if _re.search(r'(Whole Health for Pain|Office of Patient Centered|VA-employee|'
                      r'September 1, 2016|A HANDWARMING GUIDED|VHA /)', s, _re.I):
            continue
        keep.append(ln)
    return _re.sub(r'\n{3,}', '\n\n', '\n'.join(keep)).strip()

anchors = [_clean_anchor(r["text"]) for r in (json.loads(l) for l in open(GOLD))
           if "exemplars/" in r.get("src", "")][:2]

INTAKES = [
  # --- usage-universe expansion (2026-06-10, docs/qc/usage-universe.md): the
  # flywheel should practice on the world its users actually bring. ---
  ("settling", "I have surgery in the morning and I keep imagining things going wrong. Settle me."),
  ("settling", "Night shift starts in an hour. I need calm but AWAKE — don't put me to sleep."),
  ("settling", "I just read an email that made my blood boil. Ten minutes to come down before I reply."),
  ("settling", "The baby is finally down and I'm too wired to sleep. Bring me down gently."),
  ("settling", "Jet lag. It's 3am and my body thinks it's noon. Help."),
  ("settling", "I'm in the chemo chair for another two hours. Take me somewhere else."),
  ("settling", "My back pain is loud tonight. I need to be somewhere my body isn't."),
  ("settling", "Storm sounds. Heavy blanket. No alarm tomorrow. Take me down slow."),
  ("settling", "I'm lying in a hotel bed before the biggest meeting of my life. Quiet my head."),
  ("immersion", "I'm giving the best man speech at my brother's wedding. I want to feel the laugh land."),
  ("immersion", "I have a custody hearing next month. I want to rehearse staying calm and factual on the stand."),
  ("immersion", "I want to practice the moment the craving hits after dinner and I don't pour the drink."),
  ("immersion", "Let me walk through my childhood home one more time before strangers live in it."),
  ("immersion", "One more morning walk with my dog. We put him down two weeks ago."),
  ("immersion", "I want to be at my grandmother's kitchen table while she cooks. She's been gone ten years."),
  ("immersion", "I'm coming out to my parents on Sunday. I want to imagine saying it with my voice steady."),
  ("immersion", "The MRI is Friday and I'm claustrophobic. Make the tube somewhere I can stay."),
  ("immersion", "I defend my thesis in May. Let me feel the first question land and my answer come out whole."),
  ("immersion", "I want to imagine my life five years sober. Ordinary Tuesday. Just show me it's good."),
  ("immersion", "I want to be a hawk over the valley at first light. In the body, not watching it."),
  ("immersion", "Put me inside the novel I'm writing — the lighthouse, 1911, the keeper's stairs."),
  ("immersion", "I want a slow evening with my husband like before the kids. The Lisbon apartment."),
  ("immersion", "I'm singing one song at the open mic. I want my voice to come out full, not strangled."),
  ("immersion", "Mile 24. Legs screaming. I want to practice running through the wall."),
  ("immersion", "I want to stand on the summit at sunrise after six months of training."),
  ("immersion", "The deposition is next month and their lawyer will try to rattle me. Flat and factual."),
  ("immersion", "I want to imagine the version of me who already quit this job, one year on."),
  ("immersion", "First date in four years tomorrow. I want to practice listening instead of performing."),
  ("immersion", "I want to float on my back in a warm sea with absolutely nothing required of me."),
  ("immersion", "Take me to the ocean floor. Slow, dark, enormous, calm."),
  ("immersion", "I want to sit with deep time — canyons, glaciers, things that take a million years."),
  ("immersion", "Let me imagine telling my mother the truth and her actually hearing it."),
  ("immersion", "I'm learning to say no. Let me practice the meeting where I finally do."),
  ("settling", "I want to wind down and relax after a hard day."),
  ("settling", "Help me fall asleep — my mind won't switch off."),
  ("settling", "I'm anxious and need to come back down to earth."),
  ("settling", "Walk me slowly through a forest until the stress lifts."),
  ("settling", "A few quiet minutes by the ocean."),
  ("settling", "Ease the tension out of my body, head to toe."),
  ("settling", "Sit me in a warm kitchen on a slow morning."),
  ("settling", "Rain on the roof while I rest somewhere safe."),
  ("settling", "A slow walk through a garden at dusk."),
  ("settling", "Wrap me in the quiet of fresh snow falling."),
  ("settling", "Float me on my back in warm, still water."),
  ("settling", "A cabin, a fire, and nothing I have to do."),
  ("settling", "Let my breath slow until I'm barely thinking."),
  ("settling", "Lying in summer grass watching clouds."),
  ("settling", "A candlelit bath, the day washing off."),
  ("settling", "The slow hush of a library in the afternoon."),
  ("immersion", "Imagine me a year from now, having finished the thing I keep avoiding."),
  ("immersion", "Put me on stage, the moment before I begin, completely ready."),
  ("immersion", "I want to feel what it's like to be genuinely unafraid."),
  ("immersion", "Let me be someone who finishes what they start."),
  ("immersion", "The morning I move into the home I've wanted."),
  ("immersion", "Reunited with someone I miss, an ordinary afternoon together."),
  ("immersion", "Standing at the top of a climb I didn't think I could make."),
  ("immersion", "The hard thing is suddenly, quietly easy for me."),
  ("immersion", "Walking back into my hometown as the person I became."),
  ("immersion", "The day my work is finally finished and out in the world."),
  ("immersion", "Holding my newborn for the first time."),
  ("immersion", "Crossing the finish line of the race I trained a year for."),
  ("immersion", "Sitting across from my younger self, telling them it works out."),
  ("immersion", "The first morning in a city I always wanted to live in."),
  ("immersion", "Walking on stage to accept something I earned."),
  ("immersion", "Being completely, easily fluent in the language I'm learning."),
  ("immersion", "The quiet confidence of handling a hard conversation well."),
  ("immersion", "Stepping off the plane somewhere I've never been."),
  ("immersion", "The moment I forgive someone and feel it lift."),
  ("immersion", "Cooking in a kitchen that's finally, fully mine."),
  # --- batch 3 (widen coverage) ---
  ("settling", "A hammock between two trees on a warm afternoon."),
  ("settling", "The deep quiet just after the first snow."),
  ("settling", "Sinking into a hot spring under open sky."),
  ("settling", "A train at night, the dark country sliding past the window."),
  ("settling", "Lying on a dock, the water lapping the posts below."),
  ("settling", "A greenhouse full of warm earth and green smell."),
  ("settling", "The slow burn of a wood stove while it storms outside."),
  ("settling", "Floating in the warm shallows of a calm sea."),
  ("immersion", "Pulling the first loaf of bread I baked out of the oven."),
  ("immersion", "Sitting at the piano and the hard piece just flows."),
  ("immersion", "Walking into the room and the work I made is on the wall."),
  ("immersion", "The hug from someone who's proud of me."),
  ("immersion", "Speaking up in the meeting and being exactly clear."),
  ("immersion", "Paddling out and catching the wave clean."),
  ("immersion", "The morning after I finally said the hard true thing."),
  ("immersion", "Standing in the field I planted, everything grown."),
  ("immersion", "Teaching my kid to ride a bike and letting go."),
  ("immersion", "The calm of knowing the money is finally handled."),
  ("immersion", "Walking my dog at dawn, the street ours alone."),
  ("immersion", "Closing the laptop on the last day before a long rest."),
  ("immersion", "Being the steady one when everyone else panicked."),
  ("immersion", "The first real laugh after a long hard stretch."),
  ("immersion", "Stepping on stage and the nerves turn into focus."),
  ("immersion", "Coming home to a house that finally feels like home."),
]

SYS = ("You write guided sessions read aloud, slowly. Output ONLY the script — no "
       "title, no preamble, no 'Here is', and NEVER an explanatory/preachy intro about "
       "the practice or its benefits — START IN THE SCENE. VARY YOUR OPENING: do not "
       "always begin 'get comfortable, take three deep breaths' — sometimes open mid-"
       "scene, with a sound, an object, a temperature, a first step. No conclusory "
       "abstractions (gratitude, 'the practice', 'inner peace'), no named third people. "
       "COMMIT to specific, physical, concrete things "
       "the listener can see, feel, hear, smell — name real objects (a cold doorknob, "
       "rain on a window, the weight of a mug, grit underfoot). NEVER retreat to "
       "abstractions like 'a sense of calm', 'the present moment', 'let go of "
       "negativity', 'inner peace' — those are banned. Each moment, point to one real "
       "thing. Leave room for the listener to do the imagining; don't over-explain.")

def fewshot(protocol, intake):
    ex = "\n\n".join(f'EXAMPLE (notice the concrete physical detail in every line):\n"""\n{a}\n"""'
                     for a in anchors)
    rules = ("Write in the IMMERSION style: present tense, you ARE there now, hard-cut "
             "into the scene, no 'imagine that maybe' hedging."
             if protocol == "immersion" else
             "Write in the SETTLING style: slow, permissive, relaxation-led; it's fine "
             "to trail off at the end.")
    return (f"{ex}\n\nNow write a NEW guided session (~400 words) in that same concrete, "
            f"physical style for someone who asked: \"{intake}\".\n{rules}\nOutput only the script.")

# append mode. Default: skip intakes already generated (rounds accumulate).
# HEARTH_GEN_FRESH=1: generate a NEW variation for EVERY intake every pass (continuous
# mode — temperature gives a different script each time → keeps the pool growing).
done = set()
if os.path.exists(OUT) and not os.environ.get("HEARTH_GEN_FRESH"):
    done = {json.loads(l).get("intake") for l in open(OUT)}

print("loading model…", flush=True)
eng = Engine.load()
todo = [(p, i) for p, i in INTAKES if i not in done]
print(f"loaded. anchors={len(anchors)}. {len(done)} already done; generating {len(todo)} new…\n", flush=True)

n = 0
with open(OUT, "a") as f:
    for protocol, intake in todo:
        try:
            text = "".join(eng.stream(
                messages=[{"role": "system", "content": SYS},
                          {"role": "user", "content": fewshot(protocol, intake)}],
                max_tokens=700, temperature=0.75)).strip()
        except Exception as e:
            print(f"FAIL {intake[:40]}: {str(e)[:80]}", flush=True); continue
        f.write(json.dumps({"intake": intake, "protocol": protocol, "text": text,
                            "src": "generated-fewshot"}, ensure_ascii=False) + "\n")
        f.flush(); n += 1
        print(f"[{n}/{len(todo)}] {protocol:9s} {intake[:46]}  ({len(text.split())}w)", flush=True)
print(f"\ndone — {n} candidates -> {OUT}")
