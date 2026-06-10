#!/usr/bin/env python3
"""Mechanical scoreboard over QC-battery scripts — the floor of the triangulated
quality read (mechanical sieve + strict rubric + human/Claude reading; never trust
any one alone).

Parses `----- GENERATED SCRIPT ... -----` blocks out of battery logs, scores each:
  concrete  — sensory/physical commitments per 100 words (higher better)
  abstract  — AI-y abstraction retreats per 100 words (lower better)
  meta      — "welcome to this meditation" framing (any is a defect)
  guided    — second-person directing-a-listener signal per 100 words
  degen     — broken-record loop detected (postcheck.py)
Usage: score_scripts.py <log> [<log>...]
"""
import re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from imagination_engine.postcheck import degeneration_report

CONCRETE = re.compile(r"\b(feel|feeling|notice|see|look|watch|hear|listen|touch|smell|"
  r"taste|skin|hand|hands|finger|fingers|feet|foot|toes|face|jaw|shoulder|shoulders|"
  r"chest|stomach|belly|back|neck|eyes|eyelids|forehead|breath|breathe|arms|legs|knees|"
  r"palms|lips|tongue|teeth|scalp|spine|muscles|floor|ground|chair|bed|window|door|wall|"
  r"ceiling|water|sand|sun|tree|trees|leaf|leaves|grass|stone|rock|path|breeze|rain|"
  r"warmth|cold|warm|cool|rough|smooth|soft|heavy|weight|blanket|pillow|table|cup|mug|"
  r"room|wood|wooden|salt|damp|bark|petal|stream|shore|wave|waves|step|steps)\b", re.I)
ABSTRACT = re.compile(r"\b(sense of|presence|energy|journey|essence|awareness|inner peace|"
  r"peace|calmness|negativity|positivity|positive energy|present moment|mindful|"
  r"mindfulness|intention|gratitude|serenity|tranquil|tranquility|embrace|nurtur|nourish|"
  r"healing light|divine|universe|soul|spirit|vibration|abundance|manifest|oneness|"
  r"let go of|release the|deep relaxation|sense of calm|state of)\b", re.I)
AIY_META = re.compile(r"(welcome to|i'?m (so )?glad|take this time for yourself|"
  r"in this (meditation|session)|today we|let'?s begin our|thank you for joining|"
  r"this guided|in today'?s|as we begin this)", re.I)
GUIDED = re.compile(r"\b(close your eyes|your eyes|notice|imagine|picture|breathe|"
  r"your breath|take a (deep |slow )?breath|feel your|let yourself|let your|"
  r"allow your|as you breathe|you can feel|relax your)\b", re.I)

BLOCK = re.compile(r"^----- GENERATED SCRIPT \((\d+) words.*?-----$(.*?)^----- END SCRIPT -----$",
                   re.M | re.S)
LABEL = re.compile(r"^# SCENARIO: (.+)$", re.M)


def score(text: str) -> dict:
    words = max(len(text.split()), 1)
    per100 = lambda n: round(100 * n / words, 1)
    rep = degeneration_report(text)
    return {
        "words": words,
        "concrete": per100(len(CONCRETE.findall(text))),
        "abstract": per100(len(ABSTRACT.findall(text))),
        "meta": len(AIY_META.findall(text)),
        "guided": per100(len(GUIDED.findall(text))),
        "degen": rep.get("degenerate", False),
        "degen_lost": rep.get("lost_fraction", 0.0) if rep.get("degenerate") else 0.0,
    }


def main(paths):
    rows = []
    for p in paths:
        log = Path(p).read_text(encoding="utf-8", errors="replace")
        labels = LABEL.findall(log)
        for i, m in enumerate(BLOCK.finditer(log)):
            label = labels[i] if i < len(labels) else f"script {i}"
            rows.append((label[:44], score(m.group(2).strip())))
    if not rows:
        print("no GENERATED SCRIPT blocks found")
        return
    print(f"{'scenario':46s} {'words':>5s} {'conc':>5s} {'abst':>5s} {'meta':>4s} "
          f"{'guid':>5s} {'degen':>6s}")
    for label, s in rows:
        flag = f"{s['degen_lost']:.0%}" if s["degen"] else "-"
        # Calibrated against A_gold 2026-06-09: gold concreteness ranges 1.2-12.8
        # (style-dependent), so it's a soft flag only; degen + meta are hard flags
        # (zero gold exemplars trip either).
        warn = " <-- READ ME" if (s["degen"] or s["meta"] or s["abstract"] > 3
                                  or s["concrete"] < 4) else ""
        print(f"{label:46s} {s['words']:5d} {s['concrete']:5.1f} {s['abstract']:5.1f} "
              f"{s['meta']:4d} {s['guided']:5.1f} {flag:>6s}{warn}")


if __name__ == "__main__":
    main(sys.argv[1:] or ["logs/qc/battery1.log"])
