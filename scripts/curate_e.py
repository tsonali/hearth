#!/usr/bin/env python3
"""Curate grounded-QA candidates by their machine-checkable expectations.
The strictest cull of the five families: a candidate teaches the grounding
contract only if it demonstrably followed it. Appends to E_contract_curated.jsonl."""
import json, os, re

E = os.path.expanduser("~/Downloads/hearth-corpus/E-groundedqa")
GEN, GOLD = os.path.join(E, "E_generated.jsonl"), os.path.join(E, "E_contract_curated.jsonl")

REFUSAL = re.compile(r"isn'?t in your files", re.I)
ABSENCE = re.compile(r"isn'?t in your files|not (in|mentioned in) (the|your) (files|excerpts|notes)", re.I)
META = re.compile(r"\[all information|came from|according to the excerpt|based on the (provided|given)", re.I)


def keep(r) -> tuple[bool, str]:
    out, low = r["response"], r["response"].lower()
    expect = r["expect"]
    if len(out.split()) > 80:
        return False, "too long (contract is answer-then-stop)"
    if META.search(low):
        return False, "meta/citation frame in answer text"
    if expect == "refuses":
        return (True, "") if REFUSAL.search(out) and len(out.split()) < 25 else (False, "should refuse cleanly")
    if expect.startswith("contains:"):
        needles = expect.split(":", 1)[1].split("|")
        if REFUSAL.search(out):
            return False, "false refusal"
        missing = [x for x in needles if x.lower() not in low]
        return (True, "") if not missing else (False, f"missing: {missing}")
    if expect.startswith("partial:"):
        alts = expect.split(":", 1)[1].split("|")
        has_present = any(a.lower() in low for a in alts)
        names_absence = bool(ABSENCE.search(out))
        if has_present and names_absence:
            return True, ""
        return False, f"partial contract: present={has_present} absence-named={names_absence}"
    return False, "unknown expectation"


seen = set()
if os.path.exists(GOLD):
    for l in open(GOLD):
        try:
            seen.add(json.loads(l)["question"])
        except Exception:
            pass

added = scanned = 0
cuts = {}
with open(GOLD, "a") as out:
    for l in (open(GEN) if os.path.exists(GEN) else []):
        r = json.loads(l)
        scanned += 1
        ok, why = keep(r)
        if r["question"] in seen or not ok:
            if why:
                cuts[why] = cuts.get(why, 0) + 1
            continue
        seen.add(r["question"])
        out.write(json.dumps(r, ensure_ascii=False) + "\n")
        added += 1
print(f"E curate: scanned {scanned}, kept {added}; cuts: {cuts}")
