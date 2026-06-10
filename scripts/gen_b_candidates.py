#!/usr/bin/env python3
"""Generate Family-B (Secretary) training candidates — contract-native.

The old B training data was dolly/no_robots/dialogsum: generic instruction
pairs in exactly the register the Secretary's contract bans. These candidates
are generated through the REAL product prompts (utility.py's task builders,
including _BASE's bans, the register rules, and never-invent), so what survives
curation teaches the contract instead of fighting it.

Briefs sample the usage universe (docs/qc/usage-universe.md): the mail-shaped
world, transforms, high-stakes registers. curate_b.py applies the product's own
mechanical gates before anything reaches training.

Writes ~/Downloads/hearth-corpus/B-utility/B_generated.jsonl
{task, tone, brief, instruction, response}. HEARTH_GEN_FRESH=1 = regenerate all.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from imagination_engine.inference import Engine
from imagination_engine.utility import TASKS

B = os.path.expanduser("~/Downloads/hearth-corpus/B-utility")
OUT = os.path.join(B, "B_generated.jsonl")

# (task, tone, brief, instruction)
BRIEFS = [
    # drafts across the mail universe
    ("draft", "firm", "email my landlord: bathroom ceiling has leaked twice this month, the plaster is bulging, I want a repair scheduled within 10 days or I'll use my state's repair-and-deduct law", ""),
    ("draft", "warm", "email my daughter's soccer coach: thank him for the extra goalkeeper sessions, Maya's confidence is transformed, we're grateful", ""),
    ("draft", "formal", "letter to the county assessor appealing my property tax assessment: comparable homes on my street assessed 15-20% lower, I have three examples with parcel numbers I'll attach", ""),
    ("draft", "", "condolence note to my neighbor whose wife died after a long illness. We mostly talked over the fence about his tomatoes. She always waved from the porch.", ""),
    ("draft", "", "a eulogy for my aunt Rosa: came here with nothing at 19, cleaned offices nights for 30 years, put three kids and two nieces through college, never missed a Sunday dinner, terrifying at dominoes", ""),
    ("draft", "plain", "text to my brother: I can't lend him money again. Third time this year. I love him but I'm done being the backup plan. Keep the door open though.", ""),
    ("draft", "formal", "dispute letter to Visa: charge of $847.23 on March 3 from 'TechSupreme LLC' is not mine, card was in my possession, I want it reversed and a new card issued", ""),
    ("draft", "warm", "recommendation letter for my employee Dario applying to nursing school: 4 years on my team, calmest person in any crisis, taught himself phlebotomy basics volunteering weekends", ""),
    ("draft", "firm", "email to the airline: flight cancelled with 11 hours notice, rebooked me 2 days later, EU261 applies (Madrid to JFK), I want the 600 euro compensation not a voucher", ""),
    ("draft", "plain", "message to my ex about swapping weekends: I have a work conference the 21st-22nd, offering her the 14th-15th instead, keep it logistical", ""),
    ("draft", "", "toast for my best friend's wedding: met in detention junior year, he drove 6 hours when my dad was in the hospital, his wife makes him try things (sushi, therapy, hiking) and he pretends to hate all of it", ""),
    ("draft", "formal", "appeal to my health insurer: prior authorization for physical therapy denied as 'not medically necessary' but my orthopedist Dr. Liu prescribed 12 sessions post-meniscus surgery, claim number 2241-88", ""),
    # replies
    ("reply", "concise", "From: Building Management. 'Reminder: garage spot 14 is assigned to unit 3B. Vehicles parked without authorization will be towed at owner expense.'", "I AM unit 3B, that's my spot and my car. They've got their own records wrong. Polite but get it fixed."),
    ("reply", "plain", "From my mother-in-law: 'We just think it would be lovely if Christmas was at OUR house this year like it always was before you two moved. Traditions matter to family. No pressure of course!'", "We're doing Christmas at our place this year, first one in the new house, they're warmly invited. Not taking the bait on 'no pressure'."),
    ("reply", "warm", "From an old coworker: 'Hey stranger! Wild guess but — any chance you'd be open to consulting a few hours a month for our nonprofit? We can't pay much but the mission is good.'", "Yes but cap it at 4 hours/month and only after March. Glad to hear from her."),
    # summarize
    ("summarize", "", "PTA thread: Principal: the fun run is April 18 rain date April 25, we need 12 volunteers and someone with a truck. Jen: I have a truck but only after 2pm. Marco: I can do morning setup, NOT cleanup this year, last year I was there til 7. Principal: noted Marco. Aisha: t-shirt order must go in by April 1, sizes are in the spreadsheet, 14 kids still missing. Jen: also are outside food trucks allowed this year or not? Principal: checking with the district, answer by Friday. Marco: if trucks yes, my cousin does tacos.", ""),
    ("summarize", "", "Doctor visit notes my dad recorded: blood pressure better on the new dose, 132 over 80. Dr says keep walking, the knee X-ray shows arthritis not a tear so no surgery, try the compression sleeve. Next bloodwork in 3 months, before that stop the fish oil for 2 weeks. If the dizziness comes back when standing, call right away, don't wait for the appointment.", ""),
    # rewrite
    ("rewrite", "plain", "It has come to my attention that on numerous occasions, deliverables which were the responsibility of other parties have, through no initiative of my own, become tasks which I have been expected to absorb, and I find that this dynamic, if it continues to persist going forward, may not be sustainable from my perspective.", "say it like a human being, to my manager, without sounding like I'm threatening to quit"),
    ("rewrite", "warm", "Per school policy all students must submit permission slips no later than Friday. Students without slips cannot attend. No exceptions will be made. Contact the office with questions.", "I'm the room parent — make this sound friendly for the class group chat, but the deadline still has to land"),
    ("rewrite", "", "i know its last minute and im really sorry but i cant host book club tomorrow, the contractor situation turned into a whole thing, again im so so sorry, i feel terrible, maybe someone else could host or we could skip, sorry again", "less groveling, still warm, offer my place next month"),
    # extract
    ("extract", "", "Wedding planning call w/ coordinator: final headcount due to caterer May 30 HARD deadline. DJ needs the do-not-play list by June 5 and a 20-min buffer between toasts and dancing. Florist delivering 2pm day-of, someone has to be at the venue, can't be us. Mom wants to add a memorial table — coordinator says fine but decide by May 25 for layout. Open bar ends 10pm or it's $400/hr after. Officiant STILL hasn't confirmed the rehearsal time.", ""),
    ("extract", "", "Voicemail transcript from the contractor: so the inspector flagged the junction box in the attic, that's gotta be permitted separately, I can file Tuesday but it pushes drywall to the week after. Also your tile is on backorder, the blue one, til the 19th — there's a similar one in stock if you wanna come look Saturday before noon. Oh and we found some old knob-and-tube behind the kitchen wall, not dangerous yet but you'll want a quote on that eventually.", ""),
    # organize
    ("organize", "", "estate stuff for mom: call the lawyer about the trust amendment, find the deed (safe? bank box?), her car title transfer, cancel her AARP and the two magazine subscriptions, the pension survivor benefit form needs a death certificate copy (order 5 more), thank-you notes for the flowers, donate the medical equipment to the church loan closet, figure out what to do with 60 years of photo albums, sister wants the piano appraised, change the locks on the rental property, utilities out of her name", ""),
]

done = set()
if os.path.exists(OUT) and not os.environ.get("HEARTH_GEN_FRESH"):
    done = {json.loads(l).get("brief") for l in open(OUT)}

print("loading model…", flush=True)
eng = Engine.load()
todo = [b for b in BRIEFS if b[2] not in done]
print(f"generating {len(todo)} secretary candidates…", flush=True)

n = 0
with open(OUT, "a") as f:
    for task_key, tone, brief, instruction in todo:
        task = TASKS[task_key]
        system, user = task.build(brief, instruction, tone, "")
        try:
            resp = "".join(eng.stream(
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": user}],
                max_tokens=900, temperature=0.4)).strip()
        except Exception as e:
            print("FAIL", brief[:40], str(e)[:60], flush=True)
            continue
        f.write(json.dumps({"task": task_key, "tone": tone, "brief": brief,
                            "instruction": instruction, "response": resp,
                            "src": "generated-secretary"}, ensure_ascii=False) + "\n")
        f.flush(); n += 1
        print(f"[{n}/{len(todo)}] {task_key}/{tone or '-'}: {brief[:48]}", flush=True)
print(f"done — {n} -> {OUT}")
