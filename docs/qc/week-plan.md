# The Week of Five — operating flow, June 10–14, 2026

_Sonali's mandate, verbatim: "i want to develop all 5 of them... the making it
excellent, flywheeling, etc. on ALL of them... by the end of the week these 5
files are fucking awesome, better than anything else local out there."_

## The structural fix this week is built on

The flywheel improved only TWO of five tools. Imagination (A) and Companion (C)
had generate→curate→retrain loops; the Secretary trained on generic public
datasets (dolly/no_robots/dialogsum) and Build-Your-Own on alpaca — 3,000
examples of exactly the assistant-slop register our product contracts ban
("Sure! Here's...", filler openers, invented details). Every training turn
pulled against the gates QC built. Ask-Your-Files' grounding contract wasn't
trained at all.

This week all five become contract-native:
- **A** Imagination — gold/silver/harvest pipeline (existing, now decontaminated)
- **B** Secretary — NEW: briefs from the usage universe → generated through the
  REAL product prompts → mechanically culled by the product's own gates
- **C** Companion — existing pipeline + register trainers + dodge-cull
- **D** Build-Your-Own — NEW: personas × messages (incl. floor probes) through
  the real persona+floor prompts → personhood/hedge gates
- **E** Grounded-QA (the Ask-Your-Files contract) — NEW: file-contexts ×
  question types (direct/bridge/partial/refusal) → checkable curation

Flywheel rotation becomes A→B→C→D→E, one family per turn.

## Daily rhythm (through Sunday)

- **Mini**: trains continuously, 5-family rotation, best-adapter tracking.
- **Laptop**: alternates QC bank slices and corpus candidate generation.
- **Claude**: reads everything; every defect → same-day fix → bank lock;
  daily-log entry each evening (the public narrative spine).
- **Sonali** (15-min taste audits when she wants): Private Garden gold call,
  F5 own-voice listen, best/worst transcript reads per product.

## Day plan

- **Wed**: contract-native B/D/E machinery (this commit); flywheel rotation;
  first B/D/E candidate batches generated overnight on the laptop.
- **Thu**: curated B/D/E enter the training mix; ask+build bank batteries;
  imagination slice read (night-1/night-2 variety, intimacy register).
- **Fri**: pull best adapter → FULL bank regression vs Wednesday baseline
  (comparative rubric reads, not absolute); voice QC: F5 own-voice + both
  Chatterbox voices end-to-end.
- **Sat**: scale + experience — 1,000-file ask corpus, PDF through the UI,
  first-run onboarding read, session history; signed .dmg if Apple key lands.
- **Sun**: final full-bank + comparative read against Monday's product;
  week report; public daily-log narrative complete.

## Definition of "fucking awesome, better than anything else local"

Per the competitive research (docs/internal/competitive-landscape.md): no
local product does generative-personalized sessions at all, so for A the bar
is absolute quality (gold-exemplar concreteness, zero decay, register range).
For B/C/D/E the local competition is generic chat over Ollama/Jan/AnythingLLM —
the bar is: side-by-side on the bank's scenarios, Hearth's output is the one
you'd actually send/keep/return to. Friday's comparative read measures exactly
that against base-Qwen-with-no-contract as the stand-in for "generic local."
