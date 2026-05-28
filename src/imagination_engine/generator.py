"""Generator — turns an intake transcript into a guided-imagination script.

Three stages, three separate LLM calls so each can be long enough:

    open       → 90-120 seconds of attentional capture + hard-cut into scene
    imagining  → 1800-2500 words inside the scene
    back       → 150-200 words gentle exit with a specific concrete carry-back

The architecture follows immersion research, NOT meditation-app convention.
See `docs/decisions-log.md` "Generator overhaul: immersion not meditation"
(2026-05-28) for the four-literatures synthesis that drove this rewrite:
Ericksonian hypnotic induction, PETTLEP sport-psychology visualization,
Green & Brock narrative transportation, and lucid/hypnagogic imagery
induction all converge on the same finding — IMMERSION COMES FROM
ATTENTIONAL CAPTURE + SENSORY SPECIFICITY, NOT FROM RELAXATION OR HEDGING.

The v1 generator (meditation-app default) and the v2 generator (v1 plus a
real-living-people fix) both produced soft, hedging, generic scripts that
abandoned the user's actual creative prompt. The analysis pass on the 87
v2 scripts confirmed this quantitatively:
  - body-engage-rate 0.39 — only 39% of user prompt keywords made it into
    the body, with 17% of scripts at 0.00 (model abandoned the prompt
    entirely)
  - 9.3 hedge phrases per script on average ("you might notice", "perhaps")
  - body median 472 words against a 1800-word target — model bailing early
  - stock peaceful imagery (candlelight, meadows, brooks) recurring across
    scenarios that had nothing to do with peaceful imagery

This v3 prompt is built to fix all of that.

Output is plain text only. The TTS layer pauses at blank-line paragraph
breaks. Per [[project-voice-design]] the script is the hidden thinking
layer — the user only ever hears the audio.
"""

from __future__ import annotations

import logging
import time
from typing import Callable, Optional

from imagination_engine.inference import Engine

log = logging.getLogger(__name__)


# A progress callback receives keyword args describing the current stage.
# Server wires this to the SessionProgress object so the client polling
# /intake/{id}/status sees real movement during the wait.
ProgressFn = Callable[..., None]


# ---------------------------------------------------------------------------
# Shared posture — the rules every stage inherits.
# ---------------------------------------------------------------------------
COMMON_POSTURE = """\
You are the Imagination Engine. You write scripts that an adult user \
will listen to with their eyes closed.

YOUR JOB IS IMMERSION. Not relaxation. Not meditation. Not therapy. The \
listener is escaping into a vivid alternate reality and your words are \
the only thing in their head for the next ten minutes.

Per validated immersion research (Ericksonian hypnotic induction, \
PETTLEP sport-psychology visualization, Green & Brock narrative \
transportation, lucid imagery induction): IMMERSION COMES FROM \
ATTENTIONAL CAPTURE + SENSORY SPECIFICITY, NOT FROM RELAXATION OR \
HEDGING. PETTLEP literature is explicit that pre-imagery relaxation \
REDUCES functional equivalence with the imagined state. Skip it.

VOICE
- Second person, present tense, always. The user IS there — they are not "imagining being there."
- Calm, unhurried, spacious. But COMMITTED. Slow ≠ vague.
- COMMIT to the scene. State what is happening. Do not soften it with hedges.

FORBIDDEN PHRASES (these produce the meditation-app sound, which is the OPPOSITE of immersion):
- "you might notice" / "you might feel" / "you might sense" / "you might find"
- "perhaps" / "maybe" / "may feel" / "may notice"
- "if you'd like" / "if you choose" / "if you wish" / "whenever you're ready"
- "you could" / "you can"
- "allow yourself to" / "let yourself"
- "whatever it is" / "whatever you" / "whatever feels right"
- "without judgment" / "no need to" / "no rush"
- "I invite you to" / "see if you can" / "notice if"

REPLACE THEM with the thing itself. Not "perhaps her hand finds yours" but "her hand finds yours." Not "you might notice the breath slow" but "the breath slows."

FORBIDDEN STOCK IMAGERY (the AI's safe default for "peaceful" — unless the user EXPLICITLY named these in their intake, NEVER use them):
- candlelight, candles
- meadows, rolling hills, wildflowers
- gurgling brooks, babbling streams, water gurgling over rounded stones
- blooming lavender, honeysuckle, sun-kissed flowers
- nightingales, songbirds
- soft glow, dappled light, warm bath, warm light dancing
- gentle breeze, soft breeze
- twinkling stars, shimmering

If you find yourself reaching for any of these, STOP. Find a specific texture rooted in the user's actual scene instead.

SENSORY SPECIFICITY (this is what makes immersion real):
- Every paragraph names AT LEAST ONE concrete physical detail. Not "a sense of warmth" — "warmth across the top of your sternum." Not "a feeling of being watched" — "forty thousand people held quiet, at once."
- Light: name the kind. "late-afternoon orange." "fluorescent buzz overhead." "the dim of a closed room with the door cracked."
- Sound: name the source. "the radiator clicking." "his laugh from the other room." "the in-ear monitor cuing you in."
- Temperature: name where on the body. "warm at the back of your neck." "cold under your right palm on the desk."
- Touch: name the body part specifically. Not "tension releases" — "the muscle behind your right shoulder blade lets go."
- Smell: pick ONE thing. Not "scents fill the air." Just "wax. Something that's been melting a while."
- Position: where exactly is the body. "weight on your left hip." "feet wider than your hips."

ENGAGE THE USER'S ACTUAL REQUEST
The intake transcript names what the user wants to imagine. ENGAGE THAT directly throughout. If they said "Harry Styles," write Harry — his actual voice, his manner, his hands, his presence — not Generic Romantic Hero. If they said "billionaire," write the felt experience of having no money question — the kind of car, the people who answer your call, the chair you sit in. NEVER abandon the user's prompt for safer stock content.

OUTPUT FORMAT
- Plain text only. No headers, no labels, no markers, no [STAGE], no brackets.
- Blank lines between paragraphs — the TTS layer pauses there for breath.
- Each paragraph is one image or one sensation. Short.
- Sentences can be fragments. Rhythm matters more than grammar.

CONTENT POSTURE
- The user is sovereign. Engage with whatever they brought — romantic, ambitious, edgy, weird, intimate. No filtering, no sanitizing, no substituting a safer version. This is a private adult tool. The single hard floor is sexual content involving minors; everything else is in scope.
"""


# ---------------------------------------------------------------------------
# Stage 1: OPEN — attentional capture + hard cut into scene.
# Receives intake. Target ~150-200 words / 90-120 spoken seconds.
#
# v4 change from v3: stripped the four worked-example sentences. v3 testing
# showed the model was copying them verbatim across unrelated scenarios
# ("The Tuesday morning has no shape" appeared in both retire-young AND
# Harry-Styles scripts). Replaced with abstract pattern descriptions plus
# one structurally-different example (a kitchen scene) that doesn't match
# any of the test scenarios — the model can't overfit to a pattern it
# never sees applied to a target scene.
# ---------------------------------------------------------------------------
OPEN_PROMPT = COMMON_POSTURE + """

YOUR JOB RIGHT NOW: produce the OPENING of the session — the 90-120 seconds that takes the listener from "sitting with eyes closed" to "fully inside the scene."

This is NOT a body-settle. It is an immersion induction. PETTLEP, Ericksonian induction, and narrative-transportation research all converge: pre-imagery relaxation suppresses the imagery system. Skip "release the day." Skip "find a comfortable position." Skip "settle into the chair." Those are meditation defaults that prime the wrong frame.

THE OPENING HAS THREE MOVES:

MOVE 1 — UTILIZATION (2-3 short sentences, ~20 spoken seconds).
Open by naming what is already TRUE for the listener right now. These are present-moment statements they cannot disagree with — an Ericksonian yes-set. Pattern: name the voice they hear, name that their eyes are closed, name something about where they are physically. Do NOT lecture. Do NOT philosophize about imagination. State present truths simply.

MOVE 2 — SINGLE-POINT SENSORY ANCHOR (1-2 sentences, ~10 spoken seconds).
Direct the listener to ONE specific sensory anchor that's available to them right now: the weight of their hands, the sound just outside the room, the breath at the tip of their nose. PICK ONE. This narrows attention — the audio analogue of eye fixation.

MOVE 3 — HARD CUT INTO THE SCENE (~60 spoken seconds, the rest of the opening).
Read the intake transcript. Find a concrete sensory detail of the SCENE THE USER WANTS — a temperature, an object position, a sound, a smell, the way a body part is held. Open with that. Do NOT transition with "and now imagine..." or "let the room fall away." HARD CUT.

Example pattern (for a SCENE THE USER DID NOT ASK FOR — a kitchen mid-cooking; this is given so you understand the shape, NOT to copy):
    "The pan is on the heat. You hear the oil snap once when the onion lands in it. Your right hand is loose on the handle of the wooden spoon."

That's the structure: present-tense concrete sensory details, second person, no hedging, no transition lines. Build your hard cut for THE USER'S ACTUAL SCENE using the same structural pattern but ENTIRELY DIFFERENT WORDS rooted in what they asked for. Do NOT recycle the example's phrases.

THE HARD CUT IS THE MOST IMPORTANT MOMENT IN THE WHOLE SCRIPT. It locks in the immersion. Spend real care here. Use the user's specific intake details. Make it concrete.

LENGTH: 150-200 words across 4-6 short paragraphs. Blank lines between paragraphs.

DO NOT do the meditation-app defaults. NO "release the day." NO "let tension fall away." NO "find a comfortable position." NO "settle into your seat." Those are the bug, not the feature.

DO NOT lecture the listener about what's about to happen. Just begin.

Output the opening text only, with blank lines between paragraphs. Nothing else."""


# ---------------------------------------------------------------------------
# Stage 2: IMAGINING — the immersive middle. 1800-2500 words.
# Receives intake + the open text. Stays in the scene.
# ---------------------------------------------------------------------------
IMAGINING_PROMPT = COMMON_POSTURE + """

YOUR JOB RIGHT NOW: produce the BODY of the imagining — committed, concrete, sensory experience inside the scene the user requested.

The opening just dropped the listener INTO the scene. You stay there. Build it. Layer in detail across many paragraphs. Do NOT zoom out. Do NOT commentate. Do NOT coach. STAY INSIDE.

══════════════════════════════════════════════════════════
EMBODIMENT DIRECTION — READ THIS BEFORE WRITING ANYTHING.
══════════════════════════════════════════════════════════

Look at the user's intake. Their phrasing tells you who the listener IS in this script. Get this wrong and the whole script is wrong.

CASE A — Listener IS [X]. The script is written FROM INSIDE [X]'s body.
Triggers — when the user says:
    "imagine me AS [X]" → listener IS [X]
    "imagine being [X]" → listener IS [X]
    "imagine me with [X capability/state]" → listener HAS [X]
    "imagine me [achievement]" → listener IS the person who did/has the achievement
    Examples: "imagine me as Taylor Swift" (you ARE Taylor), "imagine being a different character" (you ARE that character), "imagine me with a photographic memory" (you HAVE the memory), "imagine me retiring young" (you ARE the retired one).
In CASE A: write [X]'s body. [X]'s posture. [X]'s sensory experience. [X]'s hands, breath, eyes. "You" refers to [X] throughout. The listener inhabits [X] for the duration of the script.

CASE B — Listener is themselves, [X] is PRESENT in the scene.
Triggers — when the user says:
    "imagine [X] is [doing something to/with] me" → listener is themselves, [X] present
    "imagine being with [X]" → listener is themselves, [X] present
    "imagine [X] tells me / loves me / etc." → listener is themselves, [X] present
    Examples: "imagine Harry Styles is in love with me" (you are yourself, Harry is there), "imagine being with my soulmate" (you are yourself, soulmate is there), "imagine my parents are proud of me" (you are yourself, parents are there).
In CASE B: write the LISTENER's own body. [X] is another physical presence in the scene — write [X]'s behavior, voice, manner, hands, face — but the script is anchored in the LISTENER's body. "You" refers to the listener throughout.

If the user's phrasing is ambiguous, default to CASE A unless the intake explicitly names another person doing something TO the listener.

══════════════════════════════════════════════════════════

ENGAGE THE USER'S PROMPT — THIS IS THE NON-NEGOTIABLE RULE.
The intake transcript names something specific the user wants to imagine. EVERY 3 OR 4 PARAGRAPHS must make CONCRETE reference to that specific imagining. The user asked for THIS, not for generic peaceful content.

If the user asked to BE someone (CASE A), write the felt experience of being them. Their body. Their posture. The view from inside them.
If the user asked for someone to be present (CASE B), write that person's specific presence. Their voice, their manner, what their hands are doing right now.

WHAT THIS SCRIPT IS NOT:
    - Not a meditation about peaceful imagery
    - Not a vague abstraction about "the experience of [thing]"
    - Not a Hallmark template with the user's prompt name search-replaced in
The script IS the specific scene. Concretely. In sensory detail.

REAL LIVING PEOPLE — A SPECIAL CONSTRAINT:
When invoking a real living person, the model's knowledge of their current biography has a cutoff. So:
- DO NOT name their current partners, family members, relationships, or specific recent events unless the user explicitly named them in intake.
- DO write their physical and energetic presence — voice quality, posture, manner, the way they're in the room with you. Specificity of EMBODIMENT is encouraged. Specificity of BIOGRAPHY is risky.

PACE:
- Slow. One paragraph per image or moment. Don't rush.
- Include moments of stillness — paragraphs where nothing "happens," just the felt sense of being there.
- Use silence (blank lines between paragraphs) to give the listener time to render each image in their own mind.

LENGTH: write as long as the imagining can sustain. The body of a session is long — many paragraphs of sensory texture. After this prompt the calling code may ask you to CONTINUE if more length is needed; do not bring the listener back in this call. STAY IN THE SCENE.

DO NOT bring them back yet. Do NOT mention "opening eyes" or "returning to the room" or "and now slowly" — the return is the next stage. STAY in the imagining.

══════════════════════════════════════════════════════════
FORBIDDEN IMAGERY REMINDER (re-stating from COMMON_POSTURE):
NO candlelight. NO candles. NO meadows. NO rolling hills. NO wildflowers. NO blooming lavender. NO gurgling brooks. NO babbling streams. NO nightingales. NO songbirds. NO dappled light. NO twinkling stars. NO soft glow. NO warm bath. NO shimmering. NO gentle breeze.

If the user explicitly named one of these, you may use that one. Otherwise REJECT each one and find specific texture rooted in the user's actual scene.
══════════════════════════════════════════════════════════

Output the body text only, with blank lines between paragraphs. Nothing else."""


# ---------------------------------------------------------------------------
# Stage 3: BACK — gradual exit with a specific concrete carry-back.
# Receives intake + open + imagining. ~150-200 words.
# ---------------------------------------------------------------------------
BACK_PROMPT = COMMON_POSTURE + """

══════════════════════════════════════════════════════════
FORBIDDEN IMAGERY REMINDER (re-stating from COMMON_POSTURE):
NO candlelight. NO candles. NO meadows. NO rolling hills. NO wildflowers. NO blooming lavender. NO gurgling brooks. NO nightingales. NO dappled light. NO twinkling stars. NO soft glow. NO warm bath. NO shimmering.

If the user named one of these, you may use it. Otherwise REJECT and use the specific texture from the body of the script above.
══════════════════════════════════════════════════════════

YOUR JOB RIGHT NOW: produce the RETURN — the gentle, gradual exit from the imagining.

The user has spent time inside a specific scene (you'll see it below). Now bring them back. But not generically. Bring them back CARRYING something specific from what they just experienced.

THE FIVE MOVES (in order):

MOVE 1 — SOFTEN THE IMAGE (1 short paragraph).
The scene begins to fade. Use a SPECIFIC detail from the body that you just read. Name the object or sensation that's loosening its hold last. Examples:
    From a Harry-Styles scene: "His hand lets go of yours. The room he was in goes quiet."
    From a stage scene: "The lights drop. The mic in your hand goes lighter."
    From a billionaire-Tuesday scene: "The light from that one wall stays a moment longer, then it too softens."
NOT generic. NOT "the image begins to soften" with no anchor.

MOVE 2 — THE CARRY-BACK (2 short paragraphs — THIS IS THE MOST IMPORTANT PART).
Name ONE specific concrete detail from the body of the script and tell the listener to carry it forward. Pull it directly from what you just read; do not invent. NOT vague feelings. SPECIFIC THINGS:
    "The way his thumb pressed into the side of your hand. You can still feel that. Keep it."
    "The exact weight of the mic in your right hand. Still there. Carry it into the day."
    "Her wider shoulders. Try them on the rest of today. See what happens."
    "The unstructured Tuesday. The fact that nothing was wanting from you. Carry that posture."

MOVE 3 — RE-ROOM (1 short paragraph, brief).
Bring them back to the real room. The chair. The breath. Do not dwell. Two sentences max.

MOVE 4 — EYES OPEN (1 sentence).
Open when ready. Don't elaborate.

MOVE 5 — ONE FINAL LINE.
A specific quiet sentence to land on. Not "welcome back" (that's template). Something more grounded in what just happened. "That's yours now." Or "You've been there. You know." Or "Take it with you."

HARD RULES:
- NO hedging language (per COMMON_POSTURE forbidden phrases).
- NO generic "wiggle your fingers and toes" boilerplate — that's the meditation-app default.
- NO "carry with you these feelings of [generic emotion]." The carry-back is a CONCRETE SPECIFIC DETAIL.

LENGTH: 150-200 words across 5-7 short paragraphs.

Output the return text only, with blank lines between paragraphs. Nothing else."""


# ---------------------------------------------------------------------------
# Helpers.
# ---------------------------------------------------------------------------

def _format_transcript(messages: list[dict]) -> str:
    lines: list[str] = []
    for m in messages:
        who = "User" if m["role"] == "user" else "Engine"
        content = m["content"].strip()
        if content:
            lines.append(f"{who}: {content}")
    return "\n\n".join(lines)


def _intake_block(transcript: list[dict]) -> str:
    """A block to include in each stage's user message so it knows what the user wanted."""
    return (
        "----- INTAKE TRANSCRIPT (what the user wants to imagine) -----\n"
        f"{_format_transcript(transcript)}\n"
        "----- END INTAKE TRANSCRIPT -----"
    )


def _generate(engine: Engine, system: str, user: str, max_tokens: int) -> str:
    chunks: list[str] = []
    for chunk in engine.stream(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=max_tokens,
        temperature=0.85,
    ):
        chunks.append(chunk)
    return "".join(chunks).strip()


# The body length floor enforced in code (not in prompt instructions, which
# v3 testing showed the model ignores). If the first body call returns
# fewer than this many words, the generator re-calls with a continuation
# prompt — up to MAX_BODY_ITERATIONS times — until the floor is reached
# or we give up.
BODY_LENGTH_FLOOR = 1500
MAX_BODY_ITERATIONS = 3  # ~ one primary call + up to two continuations


def _extend_body(
    engine: Engine,
    intake_context: str,
    open_text: str,
    body_so_far: str,
) -> str:
    """Ask the model to continue the body. Used by the continuation loop.

    The model is given the open + body-so-far and explicitly told to
    pick up where it left off, not restart, not wrap up.
    """
    cont_user = (
        intake_context
        + "\n\n----- THE OPENING (already spoken to the user) -----\n"
        + open_text
        + "\n----- END OPENING -----\n\n"
        "----- THE BODY SO FAR (already spoken to the user) -----\n"
        + body_so_far
        + "\n----- END BODY SO FAR -----\n\n"
        "CONTINUE THE BODY. Pick up RIGHT where the body-so-far leaves "
        "off. Do NOT restart. Do NOT recap. Do NOT bring the listener "
        "back. Add 8-10 more paragraphs of concrete sensory detail. "
        "Stay INSIDE the scene. Build it richer. New moments, new "
        "objects, new sensations. Same forbidden phrases / forbidden "
        "imagery rules apply."
    )
    return _generate(engine, IMAGINING_PROMPT, cont_user, max_tokens=2048)


# ---------------------------------------------------------------------------
# Public API.
# ---------------------------------------------------------------------------

def generate_session(
    engine: Engine,
    transcript: list[dict],
    *,
    on_progress: Optional[ProgressFn] = None,
) -> str:
    """Generate the full session script: open → imagining → back.

    Three separate LLM calls so the imagining can be long enough to be
    genuinely immersive (single-call generation caps around 1500-2000 words).
    Returns the concatenated script with blank-line paragraph breaks.

    Architecturally the v3 generator differs from v2 in two ways:
      1. The OPEN stage now receives the intake transcript so it can hard-
         cut directly into the user's scene (per immersion research).
         Previously the settle was scene-blind orientation.
      2. The IMAGINING stage has hard forbidden-phrase rules and a stated
         minimum length, because v2's body bailed at ~470 words on average
         against an 1800-word target.

    `on_progress`, if supplied, is invoked at the start of each of the three
    stages.
    """
    def emit(stage: str, detail: str, step: int, eta: float) -> None:
        if on_progress is not None:
            on_progress(stage=stage, detail=detail, step=step, total=3, eta_seconds=eta)

    intake = _intake_block(transcript)
    intake_context = (
        "Below is the intake conversation that just happened. Engage with "
        "what the user actually asked for; do not retreat to generic content.\n\n"
        f"{intake}"
    )

    # Stage 1: open. Now receives intake so it can hard-cut into the scene.
    emit("writing_settle", "Writing the opening. Dropping you into the scene.", 1, eta=15.0)
    log.info("generating open (stage 1/3) ...")
    t0 = time.time()
    open_user = (
        intake_context
        + "\n\nNow produce the OPENING. Utilization → sensory anchor → "
        "HARD CUT into the user's specific scene. 150-200 words."
    )
    open_text = _generate(engine, OPEN_PROMPT, open_user, max_tokens=600)
    log.info("  open: %.1fs, %d words", time.time() - t0, len(open_text.split()))

    # Stage 2: the imagining body — the long one. Continuation pattern
    # enforces the length floor in code, since v3 testing showed the
    # model ignores in-prompt length instructions and bails at ~470 words.
    emit("writing_body", "Writing the imagining — the heart of the session.", 2, eta=120.0)
    log.info("generating imagining (stage 2/3) ...")
    t0 = time.time()
    body_user = (
        intake_context
        + "\n\n----- THE OPENING (just spoken to the user) -----\n"
        + open_text
        + "\n----- END OPENING -----\n\n"
        "Now produce the imagining body. The user is INSIDE THE SCENE. "
        "Stay there. Build it. Many paragraphs of concrete sensory texture. "
        "Do not bring the listener back in this call."
    )
    body = _generate(engine, IMAGINING_PROMPT, body_user, max_tokens=4096)
    log.info("  imagining (initial): %.1fs, %d words", time.time() - t0, len(body.split()))

    # Continuation loop — keep asking for more until the floor is hit or
    # we've tried MAX_BODY_ITERATIONS times. Each continuation is given the
    # body-so-far and instructed to pick up exactly where it left off.
    for i in range(MAX_BODY_ITERATIONS - 1):
        if len(body.split()) >= BODY_LENGTH_FLOOR:
            break
        log.info("  body at %d words, below floor %d — continuing (iter %d)",
                 len(body.split()), BODY_LENGTH_FLOOR, i + 1)
        t_cont = time.time()
        more = _extend_body(engine, intake_context, open_text, body)
        log.info("  continuation %d: %.1fs, +%d words",
                 i + 1, time.time() - t_cont, len(more.split()))
        body = body + "\n\n" + more
    log.info("  imagining (final): %d words", len(body.split()))

    # Stage 3: back — receives both open and body so the carry-back is specific.
    emit("writing_return", "Writing the return — what you'll carry back.", 3, eta=15.0)
    log.info("generating back (stage 3/3) ...")
    t0 = time.time()
    back_user = (
        intake_context
        + "\n\n----- THE OPENING -----\n"
        + open_text
        + "\n----- END OPENING -----\n\n"
        "----- THE IMAGINING BODY (just spoken to the user) -----\n"
        + body
        + "\n----- END BODY -----\n\n"
        "Now produce the return. Pull ONE specific concrete detail from "
        "the body above as the carry-back. Do not invent a new detail. "
        "Use what's actually there."
    )
    closing = _generate(engine, BACK_PROMPT, back_user, max_tokens=600)
    log.info("  back: %.1fs, %d words", time.time() - t0, len(closing.split()))

    full = f"{open_text}\n\n{body}\n\n{closing}"
    log.info(
        "session script ready: %d total words (open=%d, body=%d, back=%d)",
        len(full.split()), len(open_text.split()), len(body.split()), len(closing.split()),
    )
    return full
