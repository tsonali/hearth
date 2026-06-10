#!/usr/bin/env python3
"""Harvest the QC batteries' best generated scripts into the A-silver pool.

The QC campaign generates dozens of full sessions across the usage universe —
the best of them (mechanically clean AND above the concreteness floor) are
better training candidates than another blind generation round, because they've
already survived the product pipeline's nets and an honest read. Survivors are
appended to A_qc_harvest.jsonl; taste_cull re-judges EVERYTHING
on the next flywheel turn, so this adds candidates, never bypasses the bar.

Usage: harvest_qc_scripts.py logs/qc/battery*.log
"""
import json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent / "qc"))
from score_scripts import score  # noqa: E402

A = Path.home() / "Downloads" / "hearth-corpus" / "A-imagination"
SILVER = A / "A_qc_harvest.jsonl"
BLOCK = re.compile(r"^----- GENERATED SCRIPT[^\n]*-----$(.*?)^----- END SCRIPT -----$",
                   re.M | re.S)
LABEL = re.compile(r"^# SCENARIO: (.+)$", re.M)

# Floors for harvest (stricter than "not broken"): clean of all hard flags AND
# concrete enough to teach. Calibrated against A_gold range (2026-06-10).
MIN_CONCRETE = 5.0
MIN_WORDS, MAX_WORDS = 500, 2600

existing = set()
if SILVER.exists():
    for line in open(SILVER):
        try:
            existing.add(re.sub(r"\s+", " ", json.loads(line)["text"])[:120])
        except Exception:
            pass

added = scanned = 0
with open(SILVER, "a") as out:
    for logpath in sys.argv[1:]:
        text = Path(logpath).read_text(errors="replace")
        labels = LABEL.findall(text)
        for i, m in enumerate(BLOCK.finditer(text)):
            scanned += 1
            script = m.group(1).strip()
            s = score(script)
            if (s["degen"] or s["collapsed"] or s.get("phrase_rep", 0) or s["meta"] or s["abstract"] > 2.5
                    or s["concrete"] < MIN_CONCRETE
                    or not (MIN_WORDS <= s["words"] <= MAX_WORDS)):
                continue
            key = re.sub(r"\s+", " ", script)[:120]
            if key in existing:
                continue
            existing.add(key)
            label = labels[i] if i < len(labels) else "unlabeled"
            out.write(json.dumps({
                "text": script, "src": f"qc-harvest:{Path(logpath).stem}",
                "intake": label, "tier": "silver",
                "note": "survived product nets + QC read; re-judged by taste_cull each turn",
            }, ensure_ascii=False) + "\n")
            added += 1
            print(f"  harvested ({s['concrete']:.1f} conc, {s['words']}w): {label[:60]}")

print(f"\nscanned {scanned} scripts, harvested {added} -> {SILVER.name}")
