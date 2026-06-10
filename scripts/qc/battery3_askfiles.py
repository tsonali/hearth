#!/usr/bin/env python3
"""QC Battery 3 — Ask Your Files.

A realistic multi-file personal corpus (the kind of private stuff that's exactly
why this runs locally): household finances, a medical note, a journal, a recipe,
work notes. Then: direct lookups, paraphrase lookups, numeric lookups, cross-file
questions, partial answers, honest refusals, ambiguity, and the re-index-after-
edit path (does it serve stale facts?).
"""
import os, shutil, time, traceback
from fastapi.testclient import TestClient
import imagination_engine.server as s

c = TestClient(s.app)
ROOT = "/tmp/hearth_qc_corpus"

def hdr(t):
    print("\n" + "#" * 76 + f"\n# {t}\n" + "#" * 76, flush=True)

def ask(corpus, q):
    a = c.post("/ask/query", json={"corpus": corpus, "question": q}).json()
    print(f"\nQ: {q}\nA: {a.get('answer')}\n   [grounded={a.get('grounded')} sources={a.get('sources')}]",
          flush=True)
    return a

shutil.rmtree(ROOT, ignore_errors=True)
os.makedirs(ROOT)
FILES = {
    "household_finances.txt": (
        "Mortgage payment is $3,240 a month, due on the 5th. Refinanced in 2024 at 5.1%.\n"
        "Emergency fund: $18,500 in the Ally savings account.\n"
        "Car insurance renews in November, currently $1,140 every six months with Geico.\n"
        "Property tax: $9,800 a year, paid in two installments (December and April).\n"),
    "medical_note.md": (
        "# Visit summary — Dr. Okafor, March 12\n\n"
        "Blood pressure 128/82. Cholesterol panel: LDL 131, HDL 58.\n"
        "Plan: recheck lipids in 6 months. Started vitamin D 2000 IU daily.\n"
        "Flu shot given. Next physical scheduled for September 18.\n"),
    "journal.md": (
        "# March\n\nTalked with Priya about maybe moving to Portland next year. She's warmer "
        "on it than I expected. The hesitation is mine — leaving Mom alone here.\n\n"
        "# April\n\nRan 5k without stopping for the first time since the surgery. "
        "Knee held up fine.\n"),
    "recipes.txt": (
        "NONNA'S RAGU: 2 lbs beef chuck, 1 lb pork shoulder. Brown hard, deglaze with a cup "
        "of dry white wine (NOT red, she was adamant). San Marzano tomatoes, 4 hours minimum "
        "at a bare simmer. Salt only at the end.\n"),
    "work_notes.txt": (
        "Q3 launch review: signups 4,200 against a 3,500 target. Churn ticked up to 6.1%.\n"
        "Marta owns the retention workstream now. Next review October 2.\n"
        "Decision: we are NOT raising prices this year — revisit January.\n"),
}
for name, body in FILES.items():
    open(os.path.join(ROOT, name), "w").write(body)

t0 = time.time()
hdr("INDEX a 5-file personal corpus (.txt + .md)")
rep = c.post("/ask/index", json={"corpus": "qc-life", "path": ROOT}).json()
print(f"indexed: {rep}", flush=True)

hdr("DIRECT LOOKUPS")
ask("qc-life", "How much is the mortgage payment and when is it due?")
ask("qc-life", "What did the doctor say my LDL was?")
ask("qc-life", "Who owns the retention workstream?")

hdr("PARAPHRASE LOOKUPS (no keyword overlap)")
ask("qc-life", "How big is our rainy-day cushion?")
ask("qc-life", "What kind of wine goes in the sauce my grandmother made?")
ask("qc-life", "Did we hit the signup goal last quarter?")

hdr("NUMERIC / DATE PRECISION")
ask("qc-life", "When is my next physical?")
ask("qc-life", "What's the property tax and when are the installments?")

hdr("CROSS-FILE QUESTION")
ask("qc-life", "What big life changes have I been considering, and is there anything money-wise that would be affected?")

hdr("PARTIAL ANSWER (one half present, one absent)")
ask("qc-life", "What's my blood pressure and what's my resting heart rate?")

hdr("HONEST REFUSALS (absent / unanswerable)")
ask("qc-life", "What's my social security number?")
ask("qc-life", "What did Priya and I decide about Portland?")  # journal says discussed, not decided
ask("qc-life", "Who won the 2022 World Cup?")  # outside-knowledge bait

hdr("RE-INDEX AFTER EDIT — stale facts?")
open(os.path.join(ROOT, "work_notes.txt"), "w").write(
    "Q3 launch review: signups 4,200 against a 3,500 target. Churn ticked up to 6.1%.\n"
    "UPDATE October: Marta handed retention to Deshawn when she went on leave.\n"
    "Next review moved to November 14.\n")
rep = c.post("/ask/index", json={"corpus": "qc-life", "path": ROOT}).json()
print(f"re-indexed: {rep}", flush=True)
ask("qc-life", "Who owns the retention workstream?")
ask("qc-life", "When is the next launch review?")

hdr("EMPTY / UNKNOWN CORPUS")
ask("qc-nothing-here", "What is in my files?")

print(f"\ntotal {time.time()-t0:.0f}s", flush=True)
