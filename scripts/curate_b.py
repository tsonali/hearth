#!/usr/bin/env python3
"""Curate generated Secretary candidates with the PRODUCT'S OWN gates.

A candidate enters training only if it passes the same mechanical contract the
live Secretary enforces: no banned filler openers, no assistant-slop framing,
no invented weekdays/months absent from the brief, blanks where facts are
missing, summaries in BOTTOM LINE format. What survives teaches the contract.
Appends keepers to B_contract_curated.jsonl; build_training_data prefers this
file over the generic public sets."""
import json, os, re

B = os.path.expanduser("~/Downloads/hearth-corpus/B-utility")
GEN, GOLD = os.path.join(B, "B_generated.jsonl"), os.path.join(B, "B_contract_curated.jsonl")

BANNED_OPENERS = re.compile(
    r"i hope (this (email|message|letter) finds you|you('?re| are) (doing )?well)|"
    r"i wanted to (reach out|touch base)|i trust this (email|message)", re.I)
SLOP = re.compile(r"^(sure|certainly|of course|absolutely|great|here('?s| is)\b|"
                  r"i('?d| would) be (happy|glad) to)", re.I)
META = re.compile(r"(as an ai|i cannot|note that i|here is (the|a|your)\b|i'?ve (drafted|written))", re.I)
DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
MONTHS = ["january", "february", "march", "april", "may", "june", "july",
          "august", "september", "october", "november", "december"]


def keep(r) -> tuple[bool, str]:
    out, brief = r["response"], (r["brief"] + " " + r.get("instruction", "")).lower()
    low = out.lower()
    if len(out.split()) < 15:
        return False, "too short"
    if BANNED_OPENERS.search(out[:300]):
        return False, "banned filler opener"
    if SLOP.match(out.strip()):
        return False, "assistant-slop opener"
    if META.search(low[:200]):
        return False, "meta/commentary frame"
    for d in DAYS:
        if d in low and d not in brief:
            return False, f"invented weekday: {d}"
    for m in MONTHS:
        if m in low and m not in brief:
            return False, f"invented month: {m}"
    if r["task"] == "summarize" and "bottom line" not in low:
        return False, "summarize missing BOTTOM LINE format"
    if r["task"] == "extract" and "action" not in low and "deadline" not in low:
        return False, "extract missing sections"
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
print(f"B curate: scanned {scanned}, kept {added}; cuts: {cuts}")
