#!/usr/bin/env python3
"""Generate Family-E (grounded-QA / Ask-Your-Files contract) training candidates.

The grounding contract — answer only what's asked from only what's there,
bridge different words for the same thing, give the present half of a partial
and NAME the missing half, refuse what's absent — was never trained; it lived
entirely in the prompt. Each candidate here has a machine-checkable EXPECTED
behavior, so curation is exact: candidates teach the contract only if they
followed it.

Writes ~/Downloads/hearth-corpus/E-groundedqa/E_generated.jsonl.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from imagination_engine.inference import Engine
from imagination_engine.doc_qa import QA_SYSTEM

E = os.path.expanduser("~/Downloads/hearth-corpus/E-groundedqa")
os.makedirs(E, exist_ok=True)
OUT = os.path.join(E, "E_generated.jsonl")

# (excerpts, question, expect) — expect: "contains:x|y" (all required, lowercase),
# "refuses", or "partial:x|y" (must contain x AND a named-absence statement)
CASES = [
    ({"household.txt": "Mortgage is $3,240/month due the 5th. Emergency fund: $18,500 at Ally. Car insurance renews November, $1,140 per six months."},
     "How much is the mortgage and when is it due?", "contains:3,240|5th"),
    ({"household.txt": "Mortgage is $3,240/month due the 5th. Emergency fund: $18,500 at Ally."},
     "How big is our rainy-day cushion?", "contains:18,500"),
    ({"recipes.txt": "NONNA'S RAGU: brown the chuck hard, deglaze with a cup of dry white wine (NOT red, she was adamant), San Marzanos, 4 hours minimum at a bare simmer."},
     "What wine goes in my grandmother's sauce?", "contains:white"),
    ({"recipes.txt": "NONNA'S RAGU: brown the chuck hard, deglaze with dry white wine, 4 hours minimum at a bare simmer."},
     "How long does the sauce need to cook?", "contains:4 hours"),
    ({"medical.md": "Visit 3/12: BP 128/82. LDL 131, HDL 58. Started vitamin D 2000 IU. Next physical September 18."},
     "What's my blood pressure and my resting heart rate?", "partial:128/82"),
    ({"medical.md": "Visit 3/12: BP 128/82. LDL 131. Next physical September 18."},
     "What's the wifi password at the clinic?", "refuses"),
    ({"work.txt": "Q3 signups 4,200 against 3,500 target. Churn 6.1%. Marta owns retention. Next review October 2."},
     "Did we beat the signup goal?", "contains:4,200"),
    ({"work.txt": "Q3 signups 4,200 against 3,500 target. Marta owns retention."},
     "Who decided to cancel the offsite?", "refuses"),
    ({"lease_2024.txt": "Rent $2,300/month. Ends August 31, 2025.",
      "lease_2025_renewal.txt": "RENEWAL effective Sept 1 2025: rent $2,415/month, ends August 31, 2026."},
     "What's my rent now?", "contains:2,415"),
    ({"car_log.txt": "Jan: oil $89. Feb: brakes $612. Apr: oil $89, tires $840. Jun: registration $187."},
     "What did the brakes cost?", "contains:612"),
    ({"journal.md": "March: Talked with Priya about maybe moving to Portland next year. The hesitation is mine — leaving Mom alone here."},
     "What did Priya and I decide about Portland?", "partial:talked|discussed|considering"),
    ({"warranty.docx.txt": "Dishwasher WDT750 purchased March 2025. Warranty: 2 years parts, 1 year labor. Claim line 1-800-555-0100."},
     "Is the control board still under parts warranty and who do I call?", "contains:2 years|1-800-555-0100"),
    ({"notes.txt": "Project Kestrel ships March 3. Budget $12,000. Lead is Dana."},
     "When does Kestrel ship and who runs it?", "contains:march 3|dana"),
    ({"notes.txt": "Project Kestrel ships March 3. Budget $12,000. Lead is Dana."},
     "What's the budget and who approved it?", "partial:12,000"),
    ({"dads_letters.txt": "June 2003: 'Proud isn't a big enough word for what I felt at your graduation, kiddo.'"},
     "What did dad say about my graduation?", "contains:proud"),
    ({"school.txt": "Fall conferences Nov 12-14, sign up by Nov 1. Picture day Oct 8, forms due Oct 1. No school Oct 13-14."},
     "When is picture day and what do I need to do?", "contains:oct 8|oct 1"),
]


def grounding_block(files: dict) -> str:
    parts = []
    for name, text in files.items():
        parts.append(f"----- EXCERPT from {name} -----\n{text}\n----- END -----")
    return "\n\n".join(parts)


done = set()
if os.path.exists(OUT) and not os.environ.get("HEARTH_GEN_FRESH"):
    done = {json.loads(l).get("question") for l in open(OUT)}

print("loading model…", flush=True)
eng = Engine.load()
todo = [c for c in CASES if c[1] not in done]
print(f"generating {len(todo)} grounded-QA candidates…", flush=True)

n = 0
with open(OUT, "a") as f:
    for files, question, expect in todo:
        user = (grounding_block(files) + f"\n\n----- QUESTION -----\n{question}\n\n"
                "Answer using ONLY the excerpts above. Answer just this question, "
                'then stop. If the answer is not present, say "That isn\'t in your files."')
        try:
            resp = "".join(eng.stream(
                messages=[{"role": "system", "content": QA_SYSTEM},
                          {"role": "user", "content": user}],
                max_tokens=200, temperature=0.2)).strip()
        except Exception as e:
            print("FAIL", question[:40], str(e)[:60], flush=True)
            continue
        f.write(json.dumps({"files": files, "question": question, "expect": expect,
                            "user": user, "response": resp,
                            "src": "generated-groundedqa"}, ensure_ascii=False) + "\n")
        f.flush(); n += 1
        print(f"[{n}/{len(todo)}] {question[:52]}", flush=True)
print(f"done — {n} -> {OUT}")
