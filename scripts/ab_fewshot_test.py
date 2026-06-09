#!/usr/bin/env python3
"""A/B experiment: does few-shotting our REAL concrete exemplars kill the AI-y voice?

Same intake, two ways:
  BASELINE  — plain "write a guided session" instruction (what base Qwen does alone)
  FEW-SHOT  — same, but preceded by 2 real human exemplars (VA beach + handwarming)
Print both. Read for concreteness: named physical things vs generic abstraction.
"""
import re, glob, os
from imagination_engine.inference import Engine

EX_DIR = os.path.expanduser("~/imagination-engine/data/exemplars/real")


def extract_script(md: str) -> str:
    """Pull just the read-aloud script text from an exemplar .md."""
    # prefer text after a '## SCRIPT' heading
    m = re.search(r"##\s*SCRIPT[^\n]*\n", md, re.I)
    body = md[m.end():] if m else md
    if not m:  # strip YAML frontmatter
        parts = md.split("---")
        if len(parts) >= 3:
            body = "---".join(parts[2:])
    lines = []
    for ln in body.splitlines():
        s = ln.strip()
        if not s:
            lines.append("")
            continue
        # drop markdown headers, bullets, provenance/license noise
        if s.startswith(("#", ">", "-", "*", "|")) or re.search(
            r"(license|provenance|source|retrieved|http|caveat|words:|—\s*$)", s, re.I):
            continue
        lines.append(s)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


exemplars = []
for p in sorted(glob.glob(os.path.join(EX_DIR, "*.md"))):
    txt = extract_script(open(p).read())
    if len(txt.split()) > 120:
        exemplars.append((os.path.basename(p), txt))

print(f"loaded {len(exemplars)} exemplars:", [e[0] for e in exemplars])
for name, txt in exemplars:
    print(f"  {name}: {len(txt.split())} words | starts: {txt[:90]!r}")

print("\nloading model…", flush=True)
eng = Engine.load()
print("loaded.\n", flush=True)

INTAKE = "I want to walk slowly through a forest and let the day's stress fall away."

baseline_user = (
    "Write a guided relaxation/visualization session (about 350 words) for someone who "
    f"asked: \"{INTAKE}\". It will be read aloud slowly. Output only the script.")

# Use up to 2 exemplars as few-shot
fewshot_blocks = "\n\n".join(
    f"EXAMPLE SESSION {i+1} (notice: it names specific physical things — steps, water, "
    f"birds, sand — never vague abstractions):\n\"\"\"\n{txt}\n\"\"\""
    for i, (_, txt) in enumerate(exemplars[:2]))
fewshot_user = (
    "Here are two real, excellent guided sessions. Study how CONCRETE and PHYSICAL they "
    "are — they name specific things you can see/feel/hear, and never retreat to vague "
    f"abstractions like 'a sense of calm' or 'the present moment'.\n\n{fewshot_blocks}\n\n"
    "Now, in that same concrete, physical, specific style, write a NEW session (about 350 "
    f"words) for someone who asked: \"{INTAKE}\". Output only the script.")

SYS = "You write guided relaxation sessions. Output only the script, no preamble."

def gen(user):
    return "".join(eng.stream(messages=[{"role": "system", "content": SYS},
                                         {"role": "user", "content": user}],
                              max_tokens=700, temperature=0.7)).strip()

print("#" * 64); print("# BASELINE (no exemplars)"); print("#" * 64)
print(gen(baseline_user), "\n", flush=True)
print("#" * 64); print("# FEW-SHOT (anchored on 2 real exemplars)"); print("#" * 64)
print(gen(fewshot_user), flush=True)
print("\n=== done ===")
