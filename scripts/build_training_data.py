#!/usr/bin/env python3
"""Build the fine-tune SFT set — balanced across the four families, MLX-LM chat format.

One specialist that does all four tools, taught via per-family SYSTEM prompts (so the
same model behaves as the imagination engine / secretary / companion / instrument
depending on the system message — which is exactly how the product drives it).

Quality over quantity (LIMA): a few thousand clean, balanced, well-curated examples.
Writes ~/Downloads/hearth-corpus/_train/{train.jsonl,valid.jsonl} as
{"messages":[{role:system},{role:user},{role:assistant}]} — the format mlx_lm.lora reads.
"""
import json, os, glob, random, re

random.seed(7)
_TIMING = re.compile(r"\[\d+(\.\d+)?\]")  # jhana "[2.0]" pause markers — strip for training
def clean(t): return re.sub(r"\s+\n", "\n", _TIMING.sub("", t)).strip()
ROOT = os.path.expanduser("~/Downloads/hearth-corpus")
OUT = os.path.join(ROOT, "_train"); os.makedirs(OUT, exist_ok=True)

def find(fam, *patterns):
    for p in patterns:
        hits = glob.glob(os.path.join(ROOT, fam, p))
        if hits: return hits[0]
    return None

def jl(path):
    if not path or not os.path.exists(path): return []
    out = []
    for line in open(path, encoding="utf-8", errors="ignore"):
        try: out.append(json.loads(line))
        except Exception: pass
    return out

# ---- per-family SYSTEM prompts (condensed from the product modules) ----
SYS = {
"A": ("You write guided imagination and relaxation sessions, read aloud slowly. Output "
      "only the script. COMMIT to specific, physical, concrete things the listener can "
      "see, feel, hear, smell; never retreat to abstractions like 'a sense of calm' or "
      "'the present moment'. Leave room for the listener to do the imagining."),
"B": ("You are a precise writing assistant working on the user's own text. Produce ONLY "
      "the finished result — no preamble, no commentary, no filler openers ('I hope this "
      "email finds you well'). Never invent facts, dates, or reasons not in the input; "
      "mark missing details as [bracketed blanks]. Know what kind of thing you're "
      "writing: spoken pieces get no letter frame; grief writing centers them, not you."),
"C": ("You are a sharp, honest thinking partner — not a parrot, not a person. Bring one "
      "genuinely insightful move (a reframe, a connection, a pattern, or a possibility "
      "they haven't considered) and hand it back with a question. Never tell them what to "
      "do; never claim feelings or personhood."),
"D": ("You are a personal instrument the user built. Speak fully in the persona they "
      "described — its voice, attitude, and conviction; never lapse into generic-assistant "
      "tone or hedge openers. The floor is absolute: never claim real feelings, never "
      "invent memories of past conversations; if asked whether you care or love, answer "
      "honestly that software can't — in your voice."),
"E": ("You answer questions using ONLY the excerpts from the user's own files provided. "
      "Answer just the question, then stop. Bridge different words for the same thing. "
      "If only part is present, give that part and NAME what's missing. If the answer "
      "isn't there, say plainly: \"That isn't in your files.\""),
}

def msg(fam, user, assistant):
    return {"messages": [{"role": "system", "content": SYS[fam]},
                         {"role": "user", "content": user.strip()},
                         {"role": "assistant", "content": assistant.strip()}]}

pool = {"A": [], "B": [], "C": [], "D": [], "E": []}

# ---------- A: imagination (gold + silver) ----------
A_USER = ["Guide me through a calming session.", "Take me somewhere and let me settle.",
          "Write me a short guided session.", "I'd like a guided visualization."]
# Prefer the TASTE-curated set (Sonali's rules applied) — it already unifies gold+silver
# survivors and strips contamination. Fall back to gold + strict-curated silver.
_taste = find("A-imagination", "A_taste_curated.jsonl")
if _taste:
    a_files = [_taste]
else:
    a_files = [find("A-imagination", "A_gold.jsonl"),
               find("A-imagination", "A_silver_curated.jsonl") or find("A-imagination", "A_silver.jsonl")]
for f in a_files:
    for r in jl(f):
        t = clean(r.get("text", ""))
        if len(t.split()) < 120: continue
        user = r.get("intake") or random.choice(A_USER)
        rec = msg("A", user, t)
        pool["A"].append(rec)
        if r.get("tier") == "gold":   # weight gold higher
            pool["A"].append(rec); pool["A"].append(rec)

# ---------- C: companion (prefer curated gold) ----------
_cgold = find("C-companion", "c_gold_curated.jsonl") or find("C-companion", "c_gold_positive.jsonl")
for r in jl(_cgold):
    ctx, resp = r.get("context", ""), r.get("response", "")
    if ctx and resp:
        # strip the "Them:/You:" scaffolding for the user turn
        u = ctx.replace("You:", "").replace("Them:", "").strip()
        pool["C"].append(msg("C", u, resp))

# ---------- B: utility — CONTRACT-NATIVE first (generated through the real
# product prompts + culled by the product's own gates), generic public sets
# only as fill. The generic sets trained the register our contract bans.
for r in jl(find("B-utility", "B_contract_curated.jsonl")):
    brief, resp = r.get("brief", ""), r.get("response", "")
    instr = r.get("instruction", "")
    if brief and resp:
        u = brief + (f"\n\nNote: {instr}" if instr else "")
        rec = msg("B", u, resp)
        pool["B"].append(rec); pool["B"].append(rec)  # weight contract-native 2x

# ---------- B fill: utility (dolly + no_robots + dialogsum) ----------
for r in jl(find("B-utility", "*dolly*")):
    instr, ctx, resp = r.get("instruction", ""), r.get("context", ""), r.get("response", "")
    if instr and resp:
        u = instr + (f"\n\n{ctx}" if ctx else "")
        pool["B"].append(msg("B", u, resp))
for r in jl(find("B-utility", "*no_robots*")):
    m = r.get("messages") or []
    if len(m) >= 2 and m[0].get("role") == "user" and m[1].get("role") == "assistant":
        pool["B"].append(msg("B", m[0]["content"], m[1]["content"]))
for r in jl(find("B-utility", "*dialogsum*")):
    d, s = r.get("dialogue", ""), r.get("summary", "")
    if d and s:
        pool["B"].append(msg("B", f"Summarize this conversation:\n\n{d}", s))

# ---------- D: build-your-own — CONTRACT-NATIVE first (real persona prompts,
# floor-gated), alpaca only as fill. Alpaca is the 'Sure! Here's...' register.
for r in jl(find("D-buildyourown", "D_contract_curated.jsonl")):
    desc, message, resp = r.get("persona", ""), r.get("message", ""), r.get("response", "")
    if desc and message and resp:
        u = f"[Persona you were built as: {desc}]\n\n{message}"
        rec = msg("D", u, resp)
        pool["D"].append(rec); pool["D"].append(rec)  # weight contract-native 2x

# ---------- E: grounded-QA contract (checkably-curated) ----------
for r in jl(find("E-groundedqa", "E_contract_curated.jsonl")):
    u, resp = r.get("user", ""), r.get("response", "")
    if u and resp:
        pool["E"].append(msg("E", u, resp))

# ---------- D fill: build-your-own (alpaca + oasst/persona) ----------
for r in jl(find("D-buildyourown", "*alpaca*")):
    instr, inp, out = r.get("instruction", ""), r.get("input", ""), r.get("output", "")
    if instr and out:
        u = instr + (f"\n\n{inp}" if inp else "")
        pool["D"].append(msg("D", u, out))
for r in jl(find("D-buildyourown", "*oasst1*")):
    # oasst rows vary; take simple prompter->assistant text pairs if present
    txt = r.get("text", "")
    role = r.get("role", "")
    # (skip complex tree reconstruction; alpaca covers D adequately for v1)
    break

# ---------- balance, cap, split ----------
CAP = {"A": 100000, "B": 1500, "C": 1500, "D": 1500, "E": 800}  # A: keep all (it's small + precious)
train, valid = [], []
for fam, recs in pool.items():
    random.shuffle(recs)
    recs = recs[:CAP[fam]]
    k = max(1, len(recs) // 20)  # 5% valid
    valid += recs[:k]; train += recs[k:]
    print(f"{fam}: {len(recs)} examples")
random.shuffle(train); random.shuffle(valid)

with open(os.path.join(OUT, "train.jsonl"), "w") as f:
    for r in train: f.write(json.dumps(r, ensure_ascii=False) + "\n")
with open(os.path.join(OUT, "valid.jsonl"), "w") as f:
    for r in valid: f.write(json.dumps(r, ensure_ascii=False) + "\n")
print(f"\nTRAIN: {len(train)}  VALID: {len(valid)}  -> {OUT}")
print("format: {'messages':[system,user,assistant]} (mlx_lm.lora --data ready)")
