#!/usr/bin/env python3
"""Build the Family C (Companion) GOLD set — SMART, honest, non-prescriptive.

Revised per Sonali (2026-06-02): more than ELIZA. We want the turns that bring
INSIGHT — a reframe, a connection, a named pattern, an unconsidered possibility —
the way a great therapist advises (by provoking reflection), NOT by telling the
person what to do. So:
  POSITIVES = reflective OR open-question OR INSIGHT/REFRAME turns, that do NOT
              prescribe an action and do NOT fake feelings.
  NEGATIVES = prescriptive ("you should/need to…") or fake-empathy turns (contrast).
Sources: AnnoMI (MI dialogue) + counsel-chat (real therapists) + Amod (counseling).
Gold stays in the private corpus, never the repo.
"""
import json, os, re, csv, textwrap

ROOT = os.path.expanduser("~/Downloads/hearth-corpus")
C = os.path.join(ROOT, "C-companion")
OUT_POS = os.path.join(C, "c_gold_positive.jsonl")
OUT_NEG = os.path.join(C, "c_gold_negative.jsonl")

# Bare reflection / open question (mirror move) — good, but not the whole story.
REFLECT = re.compile(r"\b(it sounds like|so you|so it sounds|you're saying|you feel|"
                     r"you'?re feeling|what i'?m hearing|it seems like|sounds like you)\b", re.I)
OPENQ   = re.compile(r"^(what|how|why|tell me|help me understand|when you|where do|"
                     r"what'?s it like|what would)\b", re.I)
# INSIGHT / reframe / connection / pattern / possibility — the SMART move we now want.
INSIGHT = re.compile(
    r"\b(might (be|actually)|could (be|it be)|it'?s possible that|i wonder if|what if|"
    r"underneath (that|this|it)|the real (thing|question|issue)|you keep|part of you|"
    r"on one hand|on the other hand|have you considered|what would it mean|notice that you|"
    r"you'?re calling it|reads (more )?like|the same thing|there'?s a (pattern|connection|"
    r"tension)|that'?s the (\w+ )?time you|interesting that you)\b", re.I)
# PRESCRIPTIVE — telling them what to DO (exclude: this is the line we hold).
PRESCRIBE = re.compile(r"\b(you should|you need to|you have to|you ought|you must|"
                       r"i (would |'d )?recommend|i (would |'d )?suggest you|the best thing "
                       r"(to do |is )|make sure you|what you (need|have) to do|try to)\b", re.I)
# FAKE-EMPATHY / personhood (exclude).
FAKE = re.compile(r"\b(i can understand how|i'?m here for you|i feel|i'?m so (sorry|proud|"
                  r"happy) (for|about) you|i care about you)\b", re.I)
LOGISTICS = re.compile(r"\b(is it okay if|fill(ed)? (it|this) out|screening form|"
                       r"take a look at what you put|before you leave|thanks for (coming|"
                       r"filling))\b", re.I)


def classify(resp: str):
    """Return ('pos', tag) | ('neg', why) | (None, None)."""
    t = resp.strip()
    if len(t.split()) < 4:
        return None, None
    if FAKE.search(t):
        return "neg", "fake-empathy"
    if PRESCRIBE.search(t):
        return "neg", "prescriptive"
    if LOGISTICS.search(t):
        return None, None
    if INSIGHT.search(t):
        return "pos", "insight"
    if REFLECT.search(t):
        return "pos", "reflection"
    if OPENQ.search(t) and t.rstrip().endswith("?"):
        return "pos", "open-question"
    return None, None


pos, neg = [], []

# ---- AnnoMI multi-turn ----
def ctx_of(turns, i, n=3):
    seg = turns[max(0, i - n):i]
    return "\n".join(f"{'Them' if x['role']=='client' else 'You'}: {x['text'].strip()}"
                     for x in seg if x.get('text', '').strip())

p = os.path.join(C, "annomi_motivational_interviewing.jsonl")
if os.path.exists(p):
    for line in open(p):
        turns = json.loads(line).get("turns", [])
        for i, t in enumerate(turns):
            if t.get("role") != "therapist" or i == 0: continue
            if turns[i-1].get("role") != "client": continue
            kind, tag = classify(t.get("text", ""))
            ctx = ctx_of(turns, i)
            if not ctx: continue
            rec = {"context": ctx, "response": t["text"].strip(), "src": "annomi", "tag": tag}
            (pos if kind == "pos" else neg if kind == "neg" else []).append(rec) if kind else None

# ---- counsel-chat + Amod (single Q->A) ----
def add_qa(path, src, qk, ak):
    if not os.path.exists(path): return
    for line in open(path):
        r = json.loads(line)
        q, a = str(r.get(qk, "")).strip(), str(r.get(ak, "")).strip()
        if not q or not a: continue
        # take the first 1-2 sentences of long therapist answers (the move, not the essay)
        kind, tag = classify(a)
        if not kind: continue
        rec = {"context": f"Them: {q[:600]}", "response": a[:700], "src": src, "tag": tag}
        (pos if kind == "pos" else neg).append(rec)

# counsel-chat field names vary; try common ones
for path, src in [(os.path.join(C, "counsel_chat_qa.jsonl"), "counsel-chat")]:
    if os.path.exists(path):
        sample = json.loads(open(path).readline())
        qk = next((k for k in ("question","questionText","questionTitle","Context","context") if k in sample), None)
        ak = next((k for k in ("answer","answerText","Response","response") if k in sample), None)
        if qk and ak: add_qa(path, src, qk, ak)

add_qa(os.path.join(C, "counseling_convos.jsonl"), "amod", "Context", "Response")

# de-dup positives by response text
seen = set(); pos_u = []
for r in pos:
    k = r["response"][:120]
    if k in seen: continue
    seen.add(k); pos_u.append(r)
pos = pos_u

with open(OUT_POS, "w") as f:
    for r in pos: f.write(json.dumps(r, ensure_ascii=False) + "\n")
with open(OUT_NEG, "w") as f:
    for r in neg[:600]: f.write(json.dumps(r, ensure_ascii=False) + "\n")

from collections import Counter
tags = Counter(r["tag"] for r in pos)
srcs = Counter(r["src"] for r in pos)
MAN = os.path.join(ROOT, "_manifests", "manifest.csv")
with open(MAN, "a", newline="") as f:
    csv.writer(f).writerow(["C","c_gold_positive.jsonl","C GOLD positives (smart+non-prescriptive)",
        "derived:annomi+counsel-chat+amod","derived",
        sum(len(r['response'].split()) for r in pos),"2026-06-02",
        f"{len(pos)} pairs; tags={dict(tags)}"])

print(f"POSITIVES: {len(pos)}  by tag={dict(tags)}  by src={dict(srcs)}")
print(f"NEGATIVES: {len(neg)} (saved {min(len(neg),600)})")
print("\n===== SAMPLE 'insight' POSITIVES (the smart move) =====")
shown = 0
for r in pos:
    if r["tag"] != "insight": continue
    print("\nCONTEXT:\n" + textwrap.indent(r["context"][:300], "  "))
    print("RESPONSE [" + r["src"] + "]:\n  " + r["response"][:320])
    shown += 1
    if shown >= 4: break
print("\n===== SAMPLE NEGATIVES (excluded — prescriptive/fake) =====")
for r in neg[:3]:
    print(f"  [{r['tag']}] {r['response'][:130]}")
