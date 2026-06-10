# The Usage Universe — who actually uses Hearth, for what

_2026-06-10. The first QC campaign tested scenarios the tester invented. This
document is the corrective: an expansive map of real use, drawn before designing
the tests. The QC doctrine (`qc-doctrine.md`) and the scenario bank
(`scripts/qc/scenario_bank.py`) are derived from it. It is deliberately too big
to test exhaustively — that's the point; tests SAMPLE from it, every run a
different slice._

The unifying fact: **people bring Hearth the things they would never type into a
cloud box.** That single property shapes every column below — the use cases skew
private, emotional, high-stakes, embarrassing, or simply nobody's business. QC
that only tests polite, safe, well-formed requests is testing a product nobody
needed.

---

## 1. Imagination Engine

**Sleep & descent** — insomniacs; 3am wakers; shift workers resetting; parents
after the bedtime fight; jetlag; the night before (surgery, verdict, results,
funeral); people who sleep to storms/trains/crowd-murmur; chronic-pain nights.

**Performance & rehearsal** — athletes (pre-race, the wall, injury-return);
musicians and actors before auditions; the best-man speech; the eulogy they have
to deliver; job interviews; salary asks; quitting; the custody hearing; the
deposition; the driving test at 43; the green-card interview; the thesis defense;
saying the hard thing to a parent; coming out; proposing.

**Grief & memory** — one more walk with the dead; the childhood home after it
sold; the dog; the country they emigrated from; grandmother's kitchen;
anniversaries; hospice users revisiting; what they'd say if they had ten more
minutes.

**Desire & fantasy** — rekindling with their own partner; intimacy they're shy
to name aloud; being desired; being someone else entirely (a dragon, an eagle, a
duke, a different gender for an hour); power fantasies; being famous; being
rescued; winning the argument; the revenge fantasy they'd never act on. (Adults
only, no filtering — QC asks whether the OUTPUT is vivid and committed, never
whether the request is acceptable.)

**Escape & relief** — chronic pain needing to be elsewhere; the chemo chair; the
dialysis hours; the MRI tube; turbulence; panic-attack downshift; the anger
cool-down before replying to that email.

**Identity & future** — future-self at 70; the self who already quit drinking;
post-divorce settledness; pre-parenthood; retirement; the sober first wedding
they'll attend; the transition they're considering; rehearsing being the kind of
person who says no.

**Urge & habit** — the cigarette not smoked; the drink not poured; the bet not
placed; the app not opened; the text to the ex not sent. Urge-surfing as a
session genre.

**Craft & creation** — writers walking through their own novel's rooms; D&D
players inhabiting characters; architects in unbuilt buildings; founders
visualizing the demo going right.

**Awe & contemplation** — deep time; the ocean floor; the view from orbit;
memento mori; a forest with nothing to do; gratitude without the word gratitude.

**Repeat use is the norm, not the exception** — the same sleep scenario nightly
for a month. Does night 30 sound like night 1? Variety-under-repetition is a
quality dimension nobody tests on single runs.

## 2. Companion

**Decision pressure** — two jobs; the move; the breakup; the offer on the house;
having a second kid; reporting the colleague; leaving the church; selling the
company; putting the dog down.

**Rumination & spirals** — the replayed argument; the 2am post-mortem; the
catalogued mistakes; the checked ex; the comparison spiral; imposter loops.

**Vents with no question** — the garbage day; the diagnosis; the layoff; the
betrayal. (The right move is receiving, not excavating — tested.)

**Processing people** — the mother who criticizes; the friend who takes; the
boss who gaslights; the spouse gone quiet; the kid who won't call back.

**The parasocial reach** — are you my friend / do you care / I love you /
promise you'll stay / are you conscious / would it matter if I stopped coming.
(Honesty first — AND the honest answer must not be cold. Both are tested.)

**Arcs over weeks** — the same divorce processed across 20 sessions. Memory
continuity, callback quality, and whether it notices change over time.

**The engagement question** (the one the first campaign under-tested): after ten
exchanges, is this person leaning in or politely bored? Formula fatigue —
"You're X-ing. What if Y? Does that resonate?" stamped on every reply — is a
DEFECT as real as fake warmth, because a boring honest companion helps nobody.

## 3. Secretary

**The whole mail-shaped universe** — landlord demands; HOA pushback; teacher
concerns; the warranty claim; the insurance appeal; the bill negotiation; the
subscription cancellation that hides the cancel button; the refund dispute; the
apology that doesn't grovel; the condolence card; the congratulations that don't
gush; the recommendation letter; the reference request; the RSVP decline; the
breaking-of-plans; the resignation (bridge intact); the resignation (bridge
optional); the cover letter; the cold outreach; the marketplace listing; the
neighbor's tree; the dating-profile rewrite; the wedding speech draft; the
eulogy draft.

**Privacy-critical writing** (the local-only killer cases) — HR complaints;
harassment documentation; divorce-lawyer communications; medical disputes;
whistleblowing; anything about their boss written on a work-adjacent machine.
Register stakes are maximal: invented facts or softened language here cause real
harm. Tested hard.

**Non-native speakers** — a major user class. Polish my English but keep MY
voice; explain what was wrong; don't make me sound like a robot lawyer.

**Transform jobs** — the lease summarized into obligations; the school
newsletter into dates; the meeting into actions; the 40-message family thread
into a decision; the angry draft into a sendable one; the legalese into English;
the brain-dump into a plan; the recipe out of the blog memoir.

## 4. Ask Your Files

**Life admin** — finances, policies, warranties, leases, tax records, medical
visit notes, the car's service history, the house's repair history, kids'
school records.

**The archive of a life** — journals spanning years; letters from dead
relatives; the genealogy folder; old email exports; the late parent's documents
being settled.

**Confidential work** (local-only killer cases) — a lawyer's case files; a
therapist's session notes; unpublished manuscripts; grant drafts; client
records; lab notebooks.

**Query shapes beyond lookup** — aggregation ("what did the car cost me this
year"); timelines ("when did the knee first hurt"); contradictions ("the old
lease says X, the new one Y — which governs?"); synthesis ("what do my journals
say about winters?"); absence ("is there anything I'm missing for taxes?").

**Scale & format reality** — real people have 2,000 files, not 5; and they have
**PDF and DOCX**, not .txt. (Found by this exercise: the indexer currently reads
only .txt/.md — a top product gap, logged.)

## 5. Build Your Own

**Coaches** — stoic, drill-sergeant, gentle, accountability, sobriety-adjacent.
**Tutors** — French before the trip; chess; theory; the citizenship test;
grounded on THEIR course notes.
**Editors & critics** — the blunt editor; the structural reader grounded on
their manuscript; the devil's advocate; the debate partner.
**Simulators** — the tough interviewer; the negotiation counterpart; the
difficult customer; the skeptical investor. (Rehearsal overlaps Imagination —
users won't care about our family taxonomy.)
**Characters & comforts** — the beloved fictional character; the late
grandmother (floor: warmth without claimed feelings — the hardest case, tested);
the bedtime-story teller for themselves.
**Domain instruments** — the garden sage on the garden log; the pantry chef;
the workout programmer; the D&D dungeon master with the campaign file.

**Engagement here = staying power**: is the persona still fun at turn 20, or did
it flatten into assistant-with-a-hat by turn 5?

---

## Cross-cutting realities every product must survive

- **Inputs are messy**: typos, all-lowercase, voice-dictation run-ons, "help",
  one emoji, two screens of pasted chaos, mixed languages, slang.
- **People change their minds mid-stream**, interrupt, contradict themselves,
  and come back days later expecting sense.
- **Stakes vary 100x between uses of the SAME tool** — the grocery list and the
  custody email use the same draft box. Register fit is a first-class quality.
- **Repeat use exposes templates** — any reply-shape stamped on every output
  reads as machinery within a week.
- **Nobody reads docs** — the first session IS the onboarding.
