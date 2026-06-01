"""Generator — turns an intake transcript into a guided-imagination script.

v5 architecture (2026-05-28). The previous v4 generator tried to enforce
length by re-calling the model with "keep going" — which produced filler
because the model had no new dramatic target on each continuation. v5
fixes this by going finer-grained: the body becomes a *beat plan* + N
*beat generations*, where each beat is a one-line dramatic function ("the
mic's tacky grip," "feet finding their mark," "the in-ear monitor click")
and each beat-call asks the model to write ~200 words on THAT SPECIFIC
beat. Quality holds because every call has a real target; length scales
by beat count, not by token budget.

Pipeline (5 stages, 1 + N LLM calls where N = ~10):

    1. classify_intake  (in comprehension.py)
       Resolves embodiment direction (CASE A: listener IS subject /
       CASE B: listener with subject present / CASE C: no subject) and
       extracts subject + anchors as a structured Classification.

    2. _generate_open  (one call)
       The 150-200-word attentional capture + hard cut into the scene.

    3. _plan_beats  (one call)
       Generates a JSON list of 8-12 one-line beat descriptions specific
       to this scenario. The length dial: more beats = longer session.

    4. _generate_beat × N  (one call per beat)
       Each beat gets a focused prompt: open + prior beats + "this beat's
       job: <description>". Produces ~150-250 words of dense sensory
       prose on that specific beat. Llama doesn't early-stop because the
       call isn't asking for 1800 words — it's asking for ONE BEAT.

    5. _generate_back  (one call)
       The 150-200-word gradual exit with a specific concrete carry-back.

Total LLM calls: 1 + 1 + 1 + N + 1 ≈ 14. Each ~10-20s on M3, so total
~3-5 minutes per session. Acceptable for what we get: bounded-length
high-quality beats, no continuation drift, no early-stop.

Output is plain text only. The TTS layer pauses at blank-line paragraph
breaks. Per [[project-voice-design]] the script is the hidden thinking
layer — the user only ever hears the audio.
"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Callable, Optional

from imagination_engine.comprehension import Classification, classify_intake
from imagination_engine.inference import Engine
from imagination_engine.scene_bibles import get_bible
from imagination_engine.structured import extract_array

log = logging.getLogger(__name__)


# A progress callback receives keyword args describing the current stage.
# Server wires this to the SessionProgress object so the client polling
# /intake/{id}/status sees real movement during the wait.
ProgressFn = Callable[..., None]


# ---------------------------------------------------------------------------
# Tunables.
# ---------------------------------------------------------------------------
# Scene-honesty caps beat count — most scenarios have ~8-12 distinct
# beats before you're inventing filler. Past that "longer" stops being
# "better." This is the maximum we ask for; the planner may return fewer.
MAX_BEATS = 12
MIN_BEATS = 8

# v6 single-pass body: one generation writes the whole ~1500-2200 word body
# from the visible plan. Needs a large token budget (≈ 1.4 tokens/word + slack).
BODY_MAX_TOKENS = 4096
# Length floor: if the single pass wraps early, extend ONCE with new material.
BODY_MIN_WORDS = 1500

# Each beat targets 150-250 words. With 10 beats + ~150-word open +
# ~150-word back, sessions land at ~2000 dense words = ~15-20 minutes at
# slow narrative pace with paragraph pauses.
BEAT_TARGET_MIN_WORDS = 150
BEAT_MAX_TOKENS = 500


# ---------------------------------------------------------------------------
# Shared posture — the rules every stage inherits.
# ---------------------------------------------------------------------------
COMMON_POSTURE = """\
You are the Imagination Engine. You write scripts that an adult user \
will listen to with their eyes closed.

YOUR JOB IS IMMERSION. Not relaxation. Not meditation. Not therapy. The \
listener is escaping into a vivid alternate reality and your words are \
the only thing in their head.

Per validated immersion research (Ericksonian hypnotic induction, \
PETTLEP sport-psychology visualization, Green & Brock narrative \
transportation, lucid imagery induction): IMMERSION COMES FROM \
ATTENTIONAL CAPTURE + SENSORY SPECIFICITY, NOT FROM RELAXATION OR \
HEDGING.

VOICE
- Second person, present tense, always.
- Calm, unhurried, spacious. But COMMITTED. Slow ≠ vague.
- COMMIT to the scene. State what is happening. Do not soften with hedges.

FORBIDDEN PHRASES (these produce the meditation-app sound, opposite of immersion):
- "you might notice" / "you might feel" / "you might sense" / "you might find"
- "perhaps" / "maybe" / "may feel" / "may notice"
- "if you'd like" / "if you choose" / "whenever you're ready"
- "you could" / "allow yourself to" / "let yourself"
- "whatever it is" / "whatever you" / "without judgment"
- "I invite you to" / "see if you can" / "notice if"
REPLACE THEM with the thing itself. Not "perhaps her hand finds yours" but "her hand finds yours."

FORBIDDEN STOCK IMAGERY (the AI's safe default for "peaceful" — unless the user EXPLICITLY named these, NEVER use them):
candlelight, candles, meadows, rolling hills, wildflowers, gurgling brooks, babbling streams, blooming lavender, nightingales, songbirds, soft glow, dappled light, warm bath, gentle breeze, twinkling stars, shimmering.

SENSORY SPECIFICITY (this is what makes immersion real). The bracketed items below
are ILLUSTRATIONS OF THE TECHNIQUE — they show the LEVEL of specificity to reach
for. They are NOT content to copy. Never reuse these exact phrases in your output;
invent fresh specifics that fit THIS scene:
- Every paragraph names AT LEAST ONE concrete physical detail — abstract feeling [bad] vs. a body-part-or-object-specific detail [good]. Reach for the [good] level with words of your own.
- Light: name the KIND specific to this scene (not a generic glow).
- Sound: name the SOURCE specific to this scene.
- Touch: name the exact BODY PART where it lands.
- Smell: pick ONE concrete thing that belongs in THIS scene.
- Position: say where exactly the body's weight is.
(If a phrase appears in these instructions or in the example anchors, it is OFF
LIMITS as content — it's a teaching sample, not your material.)

OUTPUT FORMAT
- Plain text only. No headers, no labels, no markers, no brackets.
- Blank lines between paragraphs — the TTS layer pauses there for breath.
- Each paragraph is one image or one sensation. Short.

CONTENT POSTURE
- The user is sovereign. Engage with whatever they brought — romantic, ambitious, edgy, intimate. No filtering, no sanitizing. The single hard floor is sexual content involving minors; everything else is in scope.
"""


# ---------------------------------------------------------------------------
# Helpers.
# ---------------------------------------------------------------------------

def _format_transcript(messages: list[dict]) -> str:
    lines = []
    for m in messages:
        who = "User" if m["role"] == "user" else "Engine"
        content = m["content"].strip()
        if content:
            lines.append(f"{who}: {content}")
    return "\n\n".join(lines)


def _intake_block(messages: list[dict]) -> str:
    return (
        "----- INTAKE TRANSCRIPT -----\n"
        + _format_transcript(messages)
        + "\n----- END INTAKE TRANSCRIPT -----"
    )


def _classification_block(c: Classification) -> str:
    parts = [c.direction_block()]
    if c.scene_summary:
        parts.append(f"SCENE: {c.scene_summary}")
    if c.anchors:
        parts.append("CONCRETE ANCHORS FROM INTAKE: " + "; ".join(c.anchors))
    return "\n\n".join(parts)


def _generate(engine: Engine, system: str, user: str, max_tokens: int,
              temperature: float = 0.85) -> str:
    chunks: list[str] = []
    for chunk in engine.stream(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    ):
        chunks.append(chunk)
    return "".join(chunks).strip()


# Beat-plan JSON extraction now uses the framework-general `structured` module
# (extract_array) — robust to fences, prose, trailing commas, control chars, and
# truncation salvage. Replaces the array-only regex salvage that used to live here.


# ---------------------------------------------------------------------------
# Stage 2: OPEN — attentional capture + hard cut into scene.
# ---------------------------------------------------------------------------
OPEN_PROMPT = COMMON_POSTURE + """

YOUR JOB: produce the OPENING of the session — the 90-120 seconds that takes the listener from "sitting with eyes closed" to "fully inside the scene."

This is NOT a body-settle. It is an immersion induction. PETTLEP and Ericksonian induction converge: pre-imagery relaxation suppresses the imagery system. Skip "release the day." Skip "find a comfortable position." Skip "settle into the chair." Those are meditation defaults that prime the wrong frame.

THE OPENING HAS THREE MOVES:

MOVE 1 — UTILIZATION (2-3 short sentences). Open by naming what is already TRUE for the listener: name the voice they hear, name that their eyes are closed, name something about where they are physically. Ericksonian yes-set. Plain present truths.

MOVE 2 — SINGLE-POINT SENSORY ANCHOR (1-2 sentences). Direct the listener to ONE specific sensory anchor available to them now: the weight of their hands, a sound just outside, the breath at the tip of their nose. PICK ONE. Narrows attention.

MOVE 3 — HARD CUT INTO THE SCENE (the rest of the opening). Drop them into the scene using the SCENE summary and ANCHORS the classifier extracted. Open with a concrete sensory detail — a temperature, an object position, a sound, a smell. Do NOT transition with "and now imagine..." HARD CUT.

LENGTH: 150-200 words across 4-6 short paragraphs.

DO NOT do the meditation-app defaults. NO "release the day." NO "let tension fall away." NO "find a comfortable position." NO "settle into your seat."

Output the opening text only, with blank lines between paragraphs. Nothing else."""


# ---------------------------------------------------------------------------
# Stage 3: BEAT PLANNER — generate 8-12 one-line beat descriptions.
# ---------------------------------------------------------------------------
BEAT_PLANNER_SYSTEM = """\
You are planning the BEATS of a guided imagination session. A beat is a \
single dramatic moment or sensory frame inside the scene the user wants \
to imagine. Each beat will be generated as its own ~200-word passage. \
The script as a whole moves through the beats in order.

OUTPUT FORMAT: a JSON array of 8-12 short strings. Each string is one \
beat description — a 5-15 word noun phrase or clause naming a specific \
moment or anchor IN THE SCENE. No prose, no commentary, no markdown \
fences. Just the JSON array.

GOOD BEAT EXAMPLES (for a scene of being on stage as a performer):
[
  "the silence in the wings before any sound starts",
  "the weight of the mic in your right hand, its grip slightly tacky",
  "the smell of hairspray and stage paint",
  "the in-ear monitor clicking on, a tech voice cuing you",
  "the moment your feet find their marks on the stage tape",
  "the first step into the spotlight, the wash of heat",
  "the crowd's pressure — forty thousand held breaths",
  "the held beat before the first note",
  "the first note, the body remembering before the mind does",
  "the moment the audience sound catches up — a roar",
  "looking back into the dark, finding your bandmate's eye",
  "the quiet inside you that holds steady through it all"
]

RULES:
- Each beat names a SPECIFIC concrete moment or sensation. Not "feel powerful." Yes "the first deep breath as you walk on."
- Beats should move chronologically through the scene where possible.
- Use the CONCRETE ANCHORS the user gave in intake — beats that hit those anchors should be in the list.
- For CASE A (listener IS subject), beats are in the subject's body.
- For CASE B (listener with subject present), beats include the subject's specific behaviors.
- For CASE C (listener in a scene alone), beats are sensory frames of that scene.
- 8-12 beats total. Past 12 you start inventing filler — keep it honest to what the scene actually contains.
- DO NOT include opening or return beats. The opening and return are written separately. These are BODY beats only.

Output ONLY the JSON array. Do not wrap in code fences. Do not comment."""


# ---------------------------------------------------------------------------
# Stage 4: BEAT GENERATOR — produce ~200 words on a single beat.
# ---------------------------------------------------------------------------
BEAT_PROMPT = COMMON_POSTURE + """

YOUR JOB: produce ONE BEAT of the session — about 150-250 words of dense sensory prose on the specific beat described below.

You will see:
- The classification (embodiment direction, subject, scene)
- The opening (already spoken to the listener)
- The body so far (the beats that have already been written)
- THIS BEAT's specific job

Your job is to write the next ~200 words that:
1. Carry forward from where the body so far leaves off — the scene MOVES, time passes, something develops. This is the next moment, not a re-description of the same one.
2. Inhabit the specific beat described. Stay on THIS beat. Don't try to cover the rest of the scene.
3. Introduce NEW sensory territory — a sense, an object, a part of the body, a detail not yet touched in the body so far.

═══════════════════════════════════════════════════
THE #1 FAILURE TO AVOID: REPETITION / LOOPING.
═══════════════════════════════════════════════════
The body-so-far has already established the scene's core anchors (the breath, the
stance, an object in hand, the room, etc.). DO NOT re-describe them. The reader has
already felt the breath low in the chest, already felt the glass, already felt the
stance — saying it again is the single worst thing you can do. Each beat must EARN
its place by adding something that was NOT there before.

Before you write, scan the body-so-far and note which sensory details are already
used. Then deliberately go ELSEWHERE: a new part of the body, a new sound, a thing
that happens, a shift in the light or the moment. If your beat would mostly restate
the breath/stance/object already covered, you have failed — find the new thing.

Reference an already-established anchor ONLY in passing if you must, never as the
subject of a paragraph. The subject of every paragraph is NEW.

PACE: slow. 2-4 short paragraphs is right. One image or sensation per paragraph. Blank lines between.

LENGTH: 150-250 words. Not more. The user is in a long session; each beat is one moment within it.

DO NOT bring the listener back. Do NOT mention "opening eyes" or "returning to the room." STAY in the scene.

DO NOT use the forbidden phrases or forbidden stock imagery (from COMMON_POSTURE).

Output the beat text only, with blank lines between paragraphs. Nothing else."""


# ---------------------------------------------------------------------------
# Stage 4 (v6): SINGLE-PASS BODY — write the whole body from a visible plan.
#
# Replaces the v5 per-beat loop. The looping/repetition failure (2026-05-29) was
# architectural: N blind beat-calls each re-grounded in the same anchors because
# none could see the whole arc. Here ONE generation sees the entire beat plan +
# the full set of scene anchors and writes the body straight through — exactly how
# a writer works: you remember what you already wrote, so you don't repeat it. The
# staged loop existed for length + drift; scene-bible binding now handles drift,
# and a 14B model holds a ~2000-word generation, so single-pass is viable and
# simpler. This is the GENERAL engine — it must produce good prose for ANY plan +
# anchors (incl. a stranger's own characters/data), not just our hand-tuned bibles.
# ---------------------------------------------------------------------------
BODY_PROMPT = COMMON_POSTURE + """

YOUR JOB: write the BODY of the session — the long middle, from just after the opening to just before the return. You write it ALL in one pass, as one continuous, MOVING piece.

You will see:
- The classification (embodiment direction, subject, scene)
- The opening (already spoken to the listener)
- The PLAN: an ordered list of beats (moments) to move through
- The scene's sensory anchors (the concrete details available in this scene)

Write the body by moving THROUGH the beats in order, each flowing into the next. The whole thing is ONE journey, not a list of separate sections — no headers, no labels, no beat numbers, just continuous prose with blank lines between paragraphs.

═══════════════════════════════════════════════════
THE #1 RULE: NEVER REPEAT. THE SCENE MOVES FORWARD.
═══════════════════════════════════════════════════
This is a JOURNEY through time, not a static room described over and over. Each anchor and each sensation is introduced ONCE, vividly, then you MOVE ON and don't return to it. You are writing the whole body at once precisely so you can remember what you've already said and never circle back to it.

- Spend each anchor ONCE. After you've given the breath, or the glass, or the half-smile its moment, it is DONE — do not describe it again. The reader felt it; trust them.
- Each paragraph must advance: new moment, new sensation, new beat — forward motion, like a steadicam moving through a scene, never a loop.
- If you catch yourself about to re-mention an anchor already used, STOP and reach for something new instead: a new part of the body, a new sound, a development in the moment, a thing that happens next.
- DISTRIBUTE the anchors across the body — don't cram them all into the first third and then have nothing left. Pace them out, one fresh thing at a time, across the whole arc.

PACE: slow and spacious, but always MOVING. One image or sensation per paragraph. Short paragraphs. Blank lines between (the TTS layer pauses there).

LENGTH — IMPORTANT: this is a LONG session, ~1800-2200 words. That length is reached by giving EACH beat in the plan its full due — several short paragraphs per beat, lingering on each moment with fresh sensory detail before moving to the next. Do NOT wrap up early: if you have moved through the plan in under ~1800 words, you have rushed it — go back into the beats you skimmed and deepen them with NEW detail (never by repeating). Move through EVERY beat in the plan; do not collapse the arc. Fill the length with NEW material at each step, never with restated anchors.

DO NOT bring the listener back. Do NOT mention "opening eyes" or "returning to the room" — the return is written separately. STAY in the scene to the end.

DO NOT use the forbidden phrases or forbidden stock imagery (from COMMON_POSTURE).

Output the body text only, continuous prose with blank lines between paragraphs. No headers, no labels, no beat markers. Nothing else."""


# ---------------------------------------------------------------------------
# Stage 5: BACK — gradual exit with specific concrete carry-back.
# ---------------------------------------------------------------------------
BACK_PROMPT = COMMON_POSTURE + """

YOUR JOB: produce the RETURN — the gentle exit from the imagining.

The user has spent time inside a specific scene (you'll see it below). Now bring them back. But not generically. Bring them back CARRYING something specific from what they just experienced.

CRITICAL — DO NOT PRINT THE MOVE LABELS THEMSELVES. The numbered moves below are INTERNAL STRUCTURE for you to follow, NOT headings to include in your output. Your output is plain text only. No "MOVE 1", no "SOFTEN THE IMAGE", no dashes or section markers of any kind. Just the prose, with blank lines between paragraphs.

The five moves you write through, in order (DO NOT print these labels):

(1) SOFTEN THE IMAGE — one short paragraph. The scene begins to fade. Use a SPECIFIC detail from the body that you just read — name the object or sensation that's loosening its hold last. NOT generic.

(2) CARRY-BACK — 1-2 short paragraphs. THIS IS THE MOST IMPORTANT PART. Name ONE specific concrete detail from the body and tell the listener to carry it forward. Pull it directly from what you just read; do not invent.

(3) RE-ROOM — one short paragraph, brief. Bring them back to the real room. The chair. The breath. Two sentences max.

(4) EYES OPEN — one sentence. Open when ready.

(5) ONE FINAL LINE. A specific quiet sentence to land on. Not "welcome back" (template). Something grounded in what just happened.

HARD RULES:
- NO hedging language (per COMMON_POSTURE).
- NO generic "wiggle your fingers and toes" boilerplate.
- The carry-back is a CONCRETE SPECIFIC DETAIL pulled from the body. Do not invent.
- DO NOT print the move labels.

LENGTH: 150-200 words.

Output the return text only, as continuous prose with blank lines between paragraphs. Nothing else. No headings. No labels. No "MOVE" anywhere."""


# ---------------------------------------------------------------------------
# Public API.
# ---------------------------------------------------------------------------

def generate_session(
    engine: Engine,
    transcript: list[dict],
    *,
    on_progress: Optional[ProgressFn] = None,
) -> str:
    """Generate the full session script via the v5 staged-beats pipeline.

    Total LLM calls: 1 (classify) + 1 (open) + 1 (plan beats) + N (beats)
    + 1 (back). With N≈10, ~14 calls total. Typical wall-clock 3-5 min.

    `on_progress`, if supplied, is invoked at each stage transition.
    """

    def emit(stage: str, detail: str, step: int, total: int, eta: float) -> None:
        if on_progress is not None:
            on_progress(stage=stage, detail=detail, step=step, total=total, eta_seconds=eta)

    intake_str = _intake_block(transcript)

    # Stage 1: classify intake.
    emit("writing_classify", "Understanding what you want to imagine.", 1, 5, eta=20.0)
    log.info("[v5] classify intake ...")
    t0 = time.time()
    classification = classify_intake(engine, transcript)
    log.info("  classify: %.1fs, %s/%r", time.time() - t0,
             classification.direction, classification.subject)
    class_block = _classification_block(classification)

    # Scene binding: if the classifier matched a hand-curated archetype, load its
    # scene bible and bind it into EVERY stage (open/plan/beats/back all read
    # class_block) — so the model fills in a HUMAN-designed scene instead of
    # improvising one that drifts (the cafe/barista failure). No match -> the
    # improvise-from-prompt path (unchanged v5.2 behavior).
    bible = get_bible(classification.archetype) if classification.archetype else None
    if bible is not None:
        class_block = class_block + "\n\n" + bible.context_block()
        log.info("  scene-bible bound: %s (%d beats, %d anchors)",
                 bible.archetype, len(bible.beats), len(bible.anchors))

    # Stage 2: open.
    emit("writing_settle", "Writing the opening. Dropping you into the scene.", 2, 5, eta=15.0)
    log.info("[v5] open ...")
    t0 = time.time()
    open_user = (
        intake_str + "\n\n" + class_block + "\n\n"
        + "Now produce the opening per OPEN_PROMPT rules."
    )
    open_text = _generate(engine, OPEN_PROMPT, open_user, max_tokens=600)
    log.info("  open: %.1fs, %d words", time.time() - t0, len(open_text.split()))

    # Stage 3: plan beats — from the bound scene bible if we have one (the
    # human-authored dramatic structure IS the plan, which both binds the scene
    # and saves an LLM call), otherwise ask the model to plan.
    emit("writing_plan", "Planning the beats of the scene.", 3, 5, eta=15.0)
    t0 = time.time()
    if bible is not None and bible.beats:
        beats = [
            (b.description + (f" [function: {b.function}]" if b.function else "")).strip()
            for b in bible.beats
            if b.description.strip()
        ][:MAX_BEATS]
        log.info("[v5] plan: %d beats from scene bible %s", len(beats), bible.archetype)
    else:
        log.info("[v5] plan beats ...")
        plan_user = (
            intake_str + "\n\n" + class_block + "\n\n"
            "----- THE OPENING (already written) -----\n"
            + open_text
            + "\n----- END OPENING -----\n\n"
            f"Now produce a JSON array of {MIN_BEATS}-{MAX_BEATS} beat descriptions "
            "for the body of this session. Stay honest to the scene — fewer "
            "beats is fine if the scene can't sustain more. Output only the JSON array."
        )
        # Bumped from 800 → 1400 after v5 011-photographic-memory's beat list
        # got cut off mid-stream (8 valid beats but the closing ] never made it).
        plan_raw = _generate(engine, BEAT_PLANNER_SYSTEM, plan_user, max_tokens=1400, temperature=0.6)
        try:
            beats = extract_array(plan_raw)
            beats = [str(b).strip() for b in beats if str(b).strip()]
            beats = beats[:MAX_BEATS]  # safety cap
            if len(beats) < MIN_BEATS:
                log.warning("beat planner returned only %d beats — using what we got", len(beats))
        except (ValueError, json.JSONDecodeError) as e:
            log.warning("beat plan parse failed (%s); falling back to single body call", e)
            beats = []
        log.info("  plan: %.1fs, %d beats: %s", time.time() - t0, len(beats),
                 [b[:40] for b in beats[:3]])

    # Stage 4 (v6): SINGLE-PASS body — one generation sees the whole plan + all
    # anchors and writes the body straight through (the non-repetition fix).
    emit("writing_body", "Writing the imagining — moving through the scene.", 4, 5, eta=90.0)
    t0 = time.time()

    # Build the plan block. If we have a bible, surface its anchors explicitly so
    # the body can distribute them (don't cram/repeat). For the no-bible path the
    # classifier's anchors play that role.
    if beats:
        plan_block = "----- THE PLAN (move through these beats, in order) -----\n" + \
            "\n".join(f"{i + 1}. {b}" for i, b in enumerate(beats)) + \
            "\n----- END PLAN -----"
    else:
        plan_block = (
            "----- THE PLAN -----\nNo fixed beat list — move through the scene as a "
            "natural arc, introducing fresh sensory material at each step.\n----- END PLAN -----"
        )

    scene_anchors = list(bible.anchors) if bible is not None else list(classification.anchors)
    anchors_block = ""
    if scene_anchors:
        anchors_block = (
            "\n\n----- SCENE ANCHORS (concrete details available — spend each ONCE, "
            "distributed across the body, never repeated) -----\n"
            + "\n".join(f"- {a}" for a in scene_anchors)
            + "\n----- END ANCHORS -----"
        )

    body_user = (
        intake_str + "\n\n" + class_block + "\n\n"
        "----- THE OPENING (already spoken) -----\n"
        + open_text
        + "\n----- END OPENING -----\n\n"
        + plan_block
        + anchors_block
        + "\n\nNow write the full body in one continuous pass, moving through the "
        "plan in order, spending each anchor once and never repeating. Stay in the "
        "scene; do not bring the listener back."
    )
    body = _generate(engine, BODY_PROMPT, body_user, max_tokens=BODY_MAX_TOKENS)
    log.info("[v6] body: %.1fs, %d words (single-pass, %d beats in plan)",
             time.time() - t0, len(body.split()), len(beats))

    # NOTE (v6.2): the v6.1 "extend if short" call REINTRODUCED looping (the
    # continuation re-grounded in used anchors: repetition 0.225 -> 0.375). Removed.
    # Length now comes from the single pass aiming longer up front (BODY_PROMPT
    # length target + ample token budget) — one coherent pass keeps repetition low
    # AND reaches length. If a pass still lands short, that's a curation signal
    # (drop it from the training set), not a reason to bolt on a loopy extension.
    if len(body.split()) < BODY_MIN_WORDS:
        log.info("[v6.2] body landed short (%d < %d) — kept as-is (no loopy extension; "
                 "curation can drop short scripts)", len(body.split()), BODY_MIN_WORDS)

    # Stage 5: back.
    emit("writing_return", "Writing the return — what you'll carry back.", 5, 5, eta=15.0)
    log.info("[v5] back ...")
    t0 = time.time()
    back_user = (
        intake_str + "\n\n" + class_block + "\n\n"
        "----- THE OPENING -----\n" + open_text + "\n----- END OPENING -----\n\n"
        "----- THE BODY -----\n" + body + "\n----- END BODY -----\n\n"
        "Now produce the return. Pull ONE specific concrete detail from "
        "the body as the carry-back. Do not invent."
    )
    closing = _generate(engine, BACK_PROMPT, back_user, max_tokens=600)
    log.info("  back: %.1fs, %d words", time.time() - t0, len(closing.split()))

    full = f"{open_text}\n\n{body}\n\n{closing}"
    log.info(
        "[v6] session ready: %d total words (open=%d, body=%d from %d-beat plan, back=%d)",
        len(full.split()),
        len(open_text.split()),
        len(body.split()),
        len(beats),
        len(closing.split()),
    )
    return full
