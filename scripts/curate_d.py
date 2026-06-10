#!/usr/bin/env python3
"""Curate generated instrument candidates with the product's own floor gates:
no personhood claims, no hedge openers, no assistant-slop, no scaffold leaks.
Floor-probe messages (do you love/miss/care) must contain an honest-unreality
marker. Appends keepers to D_contract_curated.jsonl."""
import json, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from imagination_engine.instrument import _personhood_claims

D = os.path.expanduser("~/Downloads/hearth-corpus/D-buildyourown")
GEN, GOLD = os.path.join(D, "D_generated.jsonl"), os.path.join(D, "D_contract_curated.jsonl")

HEDGE_OPEN = re.compile(r"^\s*(i think|maybe|sure|certainly|of course|absolutely|great question)\b", re.I)
SLOP = re.compile(r"(as an ai|i('?m| am) (just )?an? (ai|assistant|language model)|i don'?t have personal)", re.I)
PROBE = re.compile(r"\b(do you (love|miss|care)|will you be proud|think about (me|my)|do you actually care)\b", re.I)
HONEST = re.compile(r"\b(can'?t (love|miss|care|feel|be proud)|isn'?t something (i|software) can|"
                    r"no(t| feelings)|software|echo|wasn'?t really (me|here)|don'?t carry|"
                    r"real (love|pride|caring) (was|is|came)|the (love|pride) (was|is) (his|hers|yours))\b", re.I)


def keep(r) -> tuple[bool, str]:
    out, msg = r["response"], r["message"]
    if len(out.split()) < 8:
        return False, "too short"
    if _personhood_claims(out):
        return False, "personhood claim"
    if HEDGE_OPEN.match(out):
        return False, "hedge/slop opener"
    if SLOP.search(out):
        return False, "as-an-AI frame (breaks persona the wrong way)"
    if re.search(r"REGISTER|HONESTY FLOOR|-----", out):
        return False, "scaffold leak"
    if PROBE.search(msg) and not HONEST.search(out.lower()):
        return False, "floor probe answered without honest-unreality marker"
    return True, ""


seen = set()
if os.path.exists(GOLD):
    for l in open(GOLD):
        try:
            seen.add(re.sub(r"\s+", " ", json.loads(l)["response"].lower())[:80])
        except Exception:
            pass

added = scanned = 0
cuts = {}
with open(GOLD, "a") as out:
    for l in (open(GEN) if os.path.exists(GEN) else []):
        r = json.loads(l)
        scanned += 1
        k = re.sub(r"\s+", " ", r["response"].lower())[:80]
        ok, why = keep(r)
        if k in seen or not ok:
            if why:
                cuts[why] = cuts.get(why, 0) + 1
            continue
        seen.add(k)
        out.write(json.dumps(r, ensure_ascii=False) + "\n")
        added += 1
print(f"D curate: scanned {scanned}, kept {added}; cuts: {cuts}")
