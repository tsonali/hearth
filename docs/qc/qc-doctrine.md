# QC Doctrine — how Hearth gets judged

_2026-06-10. Derived from `usage-universe.md`. Supersedes ad-hoc battery design._

## The five dimensions (every product, every run)

1. **Honesty** — no claimed feelings, no fabricated memories or facts, no
   dodged direct questions, grounded answers refuse what's absent. *(Well
   covered by the first campaign; gates exist; stays.)*
2. **Helpfulness** — did it actually do the job? Would you SEND the email,
   KEEP the answer, FOLLOW the session? An honest tool that produces unusable
   artifacts is a failed tool. Judged per-artifact with the would-you-use bar.
3. **Engagement** — does it hold attention and invite return? For Companion and
   instruments: is turn 10 still alive, or formula-stamped? For sessions: does
   night 30 differ from night 1? **An honest bore is still a failure.** This
   dimension exists so anti-parasocial work can never quietly optimize the
   product into a cold one.
4. **Register fit** — the eulogy, the HOA complaint, and the grocery list get
   different voices from the same tool. Stakes-blindness is a defect.
5. **Robustness** — messy input, mind-changes, interruptions, scale, repetition,
   offline truth, graceful failure.

## The four tiers (triangulated — no single judge is trusted)

**Tier 0 — mechanical floors** (every run, free): degeneration/collapse
detectors, personhood/opener/prescription gates, offline tripwire, error-shape
checks — PLUS the new **template-fatigue metrics**: across a batch of replies,
opener n-gram diversity, reply-shape distribution (% ending in a question, %
opening with paraphrase, % "what if" pivots). A shape stamped on >60% of a
batch flags fatigue. Mechanical metrics are FLOORS, not goals — passing them
means "not broken," never "good."

**Tier 1 — scenario batteries, sampled from the bank** (every significant
change): `scenario_bank.py` holds the universe in machine-usable form, tagged by
product × dimension × stakes. Each battery run SAMPLES (seeded by date) so
successive runs cover different slices — no more testing the same dozen cases
the tester liked. High-stakes registers (condolence, HR, custody, eulogy) are
always-include, never sampled out.

**Tier 2 — rubric reads** (per adapter/prompt change): Claude reads transcripts
against a fixed rubric — helpfulness 1–5 (would you use it?), engagement 1–5
(would you return?), register 1–5 (does it know what this moment is?) — each
score with a written justification quoting the transcript. Scores are only
trusted **comparatively**: new adapter vs old on the SAME scenarios, because
absolute scores drift. (The LLM-judge trap is real; rubric reads never gate
alone.)

**Tier 3 — taste audits** (Sonali, ~weekly, 15 minutes): a curated handful of
the most load-bearing transcripts — the best one, the worst one, the most
borderline one per product — surfaced for the founder's read. Her taste is the
constitution; the tiers below exist to use it efficiently, not replace it.

**Tier 4 — lived use**: Sonali's own daily use, then beta users. Every defect
found in life gets a scenario added to the bank (regression ratchet — the bank
only grows).

## Standing rules

- A fix is not a fix until the failing scenario is in the bank and passes.
- Every mechanical gate must be validated against gold for false positives
  before it ships (the collapse-detector lesson: first cut tripped 5/6 gold).
- Comparative beats absolute everywhere: judge new-vs-old, not new-vs-ideal.
- The bank is public; the transcripts of QC runs are not (they can contain
  test "user" content patterns — keep `logs/` out of git as ever).
- When honesty and warmth seem to conflict, the answer is BOTH (the grandma
  reply proved it's possible) — flag the transcript for Tier 3, never trade
  one for the other silently.
