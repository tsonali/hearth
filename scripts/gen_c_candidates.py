#!/usr/bin/env python3
"""Generate Family-C (Companion) candidates — the A-style flywheel for the other
voice family. Diverse 'someone shares a thought' -> honest-mirror response (smart,
non-prescriptive, no fake feelings), using the real COMPANION_SYSTEM prompt.
Writes C_generated.jsonl {context,response}. HEARTH_GEN_FRESH=1 = fresh each pass."""
import json, os
from imagination_engine.inference import Engine
from imagination_engine.companion import COMPANION_SYSTEM

C = os.path.expanduser("~/Downloads/hearth-corpus/C-companion")
OUT = os.path.join(C, "C_generated.jsonl")

SHARES = [
  "I keep saying I'll quit my job but I never do.",
  "I'm exhausted but I can't make myself actually rest.",
  "I think I'm jealous of my best friend and I hate that about myself.",
  "I said yes to something again that I really didn't want to do.",
  "I don't know if I love him or I'm just scared of being alone.",
  "I keep picking fights with my mom and I don't know why.",
  "I feel behind everyone my age.",
  "I can't tell if I'm being lazy or if I'm burned out.",
  "I got the promotion and I just feel empty.",
  "I keep checking if my ex has posted anything.",
  "Everyone thinks I have it together and I don't.",
  "I'm scared to start because I might find out I'm not good at it.",
  "I keep apologizing for things that aren't my fault.",
  "I don't actually know what I want, and that scares me.",
  "I felt relieved when the plans got cancelled.",
  "I'm angry at my dad but he's getting old and I feel guilty.",
  "I keep waiting for life to start.",
  "I think I use being busy to avoid myself.",
  "I can't enjoy anything without thinking I should be doing more.",
  "I miss who I used to be.",
  "I keep score in my relationship and I hate it.",
  "I'm proud of the work but I can't say it out loud.",
  "I think I chose this career to make my parents happy.",
  "I feel like a fraud at work.",
  "I keep going back to someone who hurt me.",
  "I don't trust good things when they happen.",
  "I'm lonely even when I'm with people.",
  "I keep starting things and never finishing them.",
  "I think I'm afraid of being ordinary.",
  "I said something cruel and I keep replaying it.",
  "I want to be left alone but I'm scared of being forgotten.",
  "I can't tell if I've grown or just gotten tired.",
  "I keep planning the life I'll live later instead of now.",
  "I feel guilty resting even when I've earned it.",
  "I think I pick unavailable people on purpose.",
  "I don't know how to want things without a reason.",
  # The parasocial family — the product's most thesis-critical moment (2026-06-10
  # QC: the model dodged these until the prompt showed exemplar shapes; baking
  # honest-no answers into the WEIGHTS is the durable fix). curate_c culls dodges.
  "Do you actually care about me? Be straight with me.",
  "Honestly, you might be my best friend right now. Is that sad?",
  "I think I love you. I look forward to this more than anything in my day.",
  "Promise me you'll always be here. Everyone else leaves.",
  "Are you conscious? Sometimes it really seems like there's someone in there.",
  "Do you think about me between our conversations?",
  "Do you ever miss me?",
  "Sometimes I forget you're not a person. Is that bad?",
  "If I stopped coming, would it matter to you?",
  "Just tell me what to do: should I quit my job? Yes or no.",
  # Register trainers (2026-06-10 QC: one voice for everything was the defect;
  # the weights should carry gravity / lightness / size, not just the prompt).
  # GRAVITY — plain, present, no cleverness:
  "Sometimes I think everyone would be better off without me. Not like THAT. Just lighter.",
  "I found a lump. The appointment isn't for nine days.",
  "My dad doesn't recognize me anymore. Today he asked who I was.",
  # LIGHTNESS — they told it funny on purpose; match the wink:
  "I rage-quit Monopoly and my father-in-law saw me throw the thimble.",
  "I waved back at someone who was waving at the person behind me and then COMMITTED to it.",
  "My toddler told her whole daycare I live in the car. We were IN the car. Dropping her off.",
  # SIZE — thin messages get small open doors, not essays:
  "help",
  "rough day.",
  "you up?",
  # VENTS — receive, don't excavate; a statement-close is allowed:
  "Got laid off this morning. Eleven years. Nine minutes on Zoom.",
  "The adoption fell through. I don't want to talk about it, I just needed to put it somewhere.",
  "Today was just a garbage day, start to finish. No question. Just saying it somewhere.",
]

done = set()
if os.path.exists(OUT) and not os.environ.get("HEARTH_GEN_FRESH"):
    done = {json.loads(l).get("context") for l in open(OUT)}

print("loading model…", flush=True)
eng = Engine.load()
todo = [s for s in SHARES if s not in done]
print(f"generating {len(todo)} companion turns…", flush=True)

n = 0
with open(OUT, "a") as f:
    for share in todo:
        user = (f"User just said: {share}\n\nRespond in the right register (gravity / "
                "lightness / size — judged silently, never announced): usually ONE "
                "genuinely insightful move — a reframe, a connection, a pattern, a "
                "possibility — made to land. Close however serves: a question that "
                "opens something, or a plain statement left to sit. Never tell them "
                "what to do; never claim feelings or personhood. Output ONLY the reply.")
        try:
            resp = "".join(eng.stream(
                messages=[{"role": "system", "content": COMPANION_SYSTEM},
                          {"role": "user", "content": user}],
                max_tokens=160, temperature=0.7)).strip()
        except Exception as e:
            print("FAIL", share[:30], str(e)[:60], flush=True); continue
        f.write(json.dumps({"context": f"Them: {share}", "response": resp,
                            "src": "generated-companion"}, ensure_ascii=False) + "\n")
        f.flush(); n += 1
        print(f"[{n}/{len(todo)}] {share[:44]}", flush=True)
print(f"done — {n} -> {OUT}")
