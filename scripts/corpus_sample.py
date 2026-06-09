#!/usr/bin/env python3
"""Print representative full samples from the corpus for a human/Claude read."""
import json, textwrap, os, sys

ROOT = os.path.expanduser("~/Downloads/hearth-corpus")

def show(rel, n=1, maxchars=900, label=""):
    path = os.path.join(ROOT, rel)
    print("\n" + "#" * 70)
    print(f"# {label}  [{os.path.basename(path)}]")
    print("#" * 70)
    if not os.path.exists(path):
        print("  (missing)"); return
    try:
        rows = [json.loads(l) for i, l in zip(range(n * 4), open(path))]
    except Exception as e:
        print("  (read err)", e); return
    shown = 0
    for r in rows:
        if shown >= n: break
        if isinstance(r, dict):
            txt = max((str(v) for v in r.values() if isinstance(v, str)), key=len, default="")
            if len(txt) < 40:
                for key in ("messages", "conversations"):
                    if key in r:
                        txt = json.dumps(r[key], ensure_ascii=False)
                        break
            keys = list(r.keys())
        else:
            txt = str(r); keys = "(non-dict)"
        if len(txt.strip()) < 5:
            continue
        print(f"keys={keys}")
        print(textwrap.fill(txt[:maxchars], 92))
        print("…(truncated)" if len(txt) > maxchars else "")
        shown += 1

SPECS = eval(sys.argv[1]) if len(sys.argv) > 1 else []
for spec in SPECS:
    show(*spec)
