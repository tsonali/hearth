# Scene bibles — the rich canvases the engine generates against

A **scene bible** is a hand-curated YAML file describing one **archetype** of imagining
(backstage-pre-show, romantic-intimate, retire-young, etc.) with everything the engine
needs to generate an immersive, scenario-specific session WITHOUT relying on the LLM
to invent the scene from scratch.

## Why this exists

We're not asking the LLM to imagine a scene from "imagine me as Taylor Swift." We're
asking it to *fill in* a scene we've already imagined. The LLM does the prose; the
scene comes from a human (Sonali) who knows what real immersion looks like.

Without this, the LLM defaults to its safe meditation-app voice and the result is
generic peaceful content. With this, the model has a rich specific canvas and can
spend its capacity on prose quality instead of scene invention.

## How it gets used

1. User finishes intake ("imagine me as Taylor Swift").
2. The classifier looks at the intake and maps it to an archetype — `backstage-pre-show`.
3. The generator loads `backstage-pre-show.yaml`.
4. The bible's `anchors` and `beats` become the bones of the script. The LLM writes the
   flesh — paragraph by paragraph, with each beat's specific dramatic function as
   its target.
5. User-provided specifics from intake (e.g. they named a particular tour) override
   bible defaults. If no specifics given, bible defaults stand.

## File format

```yaml
archetype: <slug>                   # filename matches: <slug>.yaml

# What user phrasings trigger this archetype. The classifier matches against these.
# Use natural language patterns, not regex. The classifier interprets.
trigger_phrases:
  - "imagine me as <a performer>"
  - "imagine being on stage"
  - "imagine <celebrity> before a show"

# CASE A (listener IS subject) or CASE B (listener with subject present)
# or CASE C (no specific subject). See comprehension.py.
direction: case_a

# The scene — what the listener is in.
scene:
  where: "<one sentence, specific>"
  when: "<one sentence, specific>"
  who_else: "<who else is present and what they're doing, or null>"
  mood: "<one sentence about the felt quality of the moment>"

# The sensory anchors — concrete details the body of the script SHOULD hit.
# 7-12 of these. Body-and-object-specific. Not abstract.
# These get passed to every beat generator call.
anchors:
  - "<short noun phrase naming a specific sensory thing>"
  - "<another>"
  ...

# The beats — the dramatic structure of the body of the session.
# 8-12 beats. Each is a moment WITHIN the scene. Each beat gets its own
# LLM call producing ~200 words.
beats:
  - description: "<one-line beat description — a moment, a sensation, a turn>"
    function: "<what this beat does dramatically (establishes / deepens / shifts / lingers)>"
  - description: "..."
    function: "..."

# Things to NOT do for this scenario — common LLM failure modes specific to this archetype.
forbidden_specifics:
  - "<don't do this>"
  - "<don't do that>"

# Voice/style notes specific to this archetype.
style_notes:
  - "<observation about what real immersion in this scene requires>"
```

## Writing a good scene bible

The point of the bible is **specificity that doesn't require the user to provide it.**
A great scene bible answers: "If a stranger came to you and said five words about
wanting to imagine THIS, what would you tell them about what that's like?"

**Anchors are bodies and objects, not abstractions.** Not "a sense of warmth" —
"warmth across the top of your sternum." Not "her presence" — "her hand on the
small of your back."

**Beats are moments, not topics.** Not "the body" or "the breath" — "the second
before the boot heel touches the stage tape." Each beat should be a thing that
happens, or a thing the listener notices, or a turn in the inner state.

**Forbidden specifics** is where you encode the lessons from failed generations.
For backstage-pre-show that might be "don't name the tour unless user did";
for romantic-intimate, "don't name a specific person unless user did."

**Style notes** capture what the LLM keeps getting wrong about this archetype.
"This is the COLD focus, not romantic warmth" or "Use breath-level pacing — one
sensation per paragraph, no rush."

## The archetype list (initial draft — to fill in)

- `backstage-pre-show` — being a performer about to take a stage
- `romantic-intimate` — being with a specific present person who loves you
- `retire-young` — having no financial concern, no obligation, a quiet day
- `different-personality` — being a calmer/braver/quieter version of yourself
- `achievement-moment` — the specific moment of having done a hard thing
- `counterfactual-other-life` — having taken a different path
- `future-self-arriving` — being yourself a decade from now, looking back
- `power-quiet` — having a specific capability used in a quiet way
- `historical-being` — being a specific historical figure in a documented moment
- `place-deep` — being in a specific evocative place, no narrative, just being

These are roughly the archetypes that cover the test_scenarios.py set. As more
edge cases come up, add bibles.

## When a user prompt doesn't match any archetype

The classifier returns `archetype: null` and the generator falls through to
pure-prompt generation (the current v5.2 behavior). The disclaimer flag for
"experimental scenarios" can surface in the UI for these.
