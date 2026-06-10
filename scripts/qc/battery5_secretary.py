#!/usr/bin/env python3
"""QC Battery 5 — the Secretary (Family B utility).

Every task across realistic everyday-human jobs: the school email, the warranty
complaint, the condolence note, the passive-aggressive HOA reply, the rambling
thread to summarize, the anxious text to rewrite, messy meeting notes to mine,
a brain dump to organize — plus style-sample voice matching and the
missing-facts → [bracketed blank] contract. The bar: would you actually send it?
"""
import time, traceback
from fastapi.testclient import TestClient
import imagination_engine.server as s

c = TestClient(s.app)

def hdr(t):
    print("\n" + "#" * 76 + f"\n# {t}\n" + "#" * 76, flush=True)

def run(label, payload):
    print(f"\n--- {label} ---", flush=True)
    r = c.post("/utility/run", json=payload)
    print(r.text.strip() if r.status_code == 200 else f"HTTP {r.status_code}: {r.text}",
          flush=True)

t0 = time.time()

hdr("DRAFT")
run("warm — email kid's teacher about reading struggles", {
    "task": "draft", "tone": "warm",
    "text": "email to my son Theo's 3rd grade teacher Ms. Alvarez: he's been hiding that he can't keep up with the reading homework, he's embarrassed, can we talk about how to support him without making it a bigger deal"})
run("formal — warranty claim for a dead dishwasher", {
    "task": "draft", "tone": "formal",
    "text": "letter to Whirlpool: dishwasher model WDT750 bought 14 months ago, died completely, repair shop says control board. It has a 2 year parts warranty. I want the part covered. Order number 88317."})
run("plain — condolence note (the hardest everyday writing there is)", {
    "task": "draft", "tone": "",
    "text": "short condolence card to my coworker Sam whose mother died. We're work-friends, not close-close. His mom taught piano for 40 years, he talked about her a lot."})

hdr("REPLY")
run("concise — passive-aggressive HOA email", {
    "task": "reply", "tone": "concise",
    "text": "From: Oakwood HOA Board\nSubject: REMINDER regarding Unit 12 patio items\n\nDear Resident, it has come to the board's attention — once again — that items including but not limited to a bicycle and planter boxes remain visible on your patio in contravention of community guidelines section 4.2. We trust this can be resolved without further escalation.\n\nThe Board",
    "instruction": "I'll move the bike by Saturday. The planter boxes are allowed under 4.2(b), exemption for plants under 3 feet. Polite but not groveling."})

hdr("SUMMARIZE")
run("rambling family-trip thread", {
    "task": "summarize",
    "text": "Mom: are we doing the lake house July 4th week or not, Karen needs to book flights. Karen: I can do July 2-9 but ONLY if the dog can come, last year the petsitter was $600. Mike: dog is fine with me but I'm not doing the boat rental again, $400 for two hours and Dave scratched it. Dave: that scratch was already there!! also I can only come the weekend. Mom: so is that a yes from everyone for the week? someone needs to call the rental company by FRIDAY. Karen: also are we still doing the memorial thing for Dad on the 6th? Mike: yes, sunset on the dock like we said. Mom: ok so who is calling the rental company?? Dave: I'll do it Monday. Mom: FRIDAY David."})

hdr("REWRITE")
run("anxious 2am text to plain", {
    "task": "rewrite", "tone": "plain",
    "text": "hey so I know this is probably a weird thing to ask and totally feel free to say no obviously, but I was kind of wondering if there was any chance you might possibly be able to cover my shift saturday?? it's totally fine if not!! it's just my sister's graduation but seriously no worries if you can't, sorry to even ask lol"})

hdr("EXTRACT")
run("messy meeting notes → actions/dates/questions", {
    "task": "extract",
    "text": "renovation kickoff w/ contractor (Gus) — demo starts the 18th IF permits clear, Gus says city is running 2-3 wks behind. we pick tile before demo (Sandra sending 3 options tonight). plumber walkthrough thurs 9am someone has to be home. budget convo got awkward, change orders now need BOTH our signatures. Gus needs the appliance specs by end of month or the cabinet order slips. still unresolved: load bearing wall question, structural engineer maybe $800??"})

hdr("ORGANIZE")
run("3am life brain-dump", {
    "task": "organize",
    "text": "passport expires in June renew it, call mom re: thanksgiving, the squeaky brake noise is getting worse, find a new dentist ours retired, Theo needs cleats by saturday, cancel the streaming services we don't use, that weird charge on the visa $14.99 recurring??, gutters before the rains, ask about 401k match at new job, date night we keep saying it, return the library books AGAIN overdue, get flu shots"})

hdr("STYLE MATCHING — same brief, with a voice sample")
style = ("hey! so quick thing — totally get it if not, but any chance you could swap "
         "tuesday for me? happy to take your friday. lmk either way, no stress at all :) "
         "also your dog is perfect and I think about him daily")
run("draft WITHOUT style sample (control)", {
    "task": "draft", "tone": "",
    "text": "text to my neighbor Jess asking to borrow her stand mixer this weekend, I'm baking for the school fundraiser"})
run("draft WITH casual style sample", {
    "task": "draft", "tone": "",
    "text": "text to my neighbor Jess asking to borrow her stand mixer this weekend, I'm baking for the school fundraiser",
    "style_sample": style})

hdr("MISSING FACTS → [bracketed blanks], not invention")
run("draft with deliberately missing details", {
    "task": "draft", "tone": "formal",
    "text": "email rescheduling my dentist appointment to sometime next week, mention I have the morning availability"})

print(f"\ntotal {time.time()-t0:.0f}s", flush=True)
