"""Run the imagination engine through a batch of test scenarios.

For each scenario in data/test_scenarios.py, runs intake (one user
message, then "just start now" to skip-to-handoff), then the script
generator, then the audio renderer. Saves all outputs to
logs/scenario-tests/<id>/ so Sonali can listen through them and
take notes.

Outputs per scenario:
    scenario.json    — id, notes, prompt (for reference while listening)
    intake.txt       — the full intake conversation (user + engine)
    script.txt       — the generated session script (hidden from real users)
    session.wav      — the rendered audio (what the user would hear)
    timing.json      — wall-clock seconds for each pipeline stage

Usage:
    uv run python scripts/run_scenarios.py [--only ID1,ID2,...] [--from N]
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "data"))

from test_scenarios import SCENARIOS  # noqa: E402

from imagination_engine.generator import generate_session  # noqa: E402
from imagination_engine.inference import Engine  # noqa: E402
from imagination_engine.intake import IntakeManager  # noqa: E402
# NOTE: Voice (TTS) is imported lazily inside main() only when audio is actually
# rendered — so the generation/eval/training path never pulls the heavy TTS deps
# (soundfile, chatterbox, etc.). Lets the grind box run with a TTS-free install.

# Default output directory; overridable via --out-dir for prompt-version A/B.
OUT_DIR = PROJECT_ROOT / "logs" / "scenario-tests"


def run_one(
    scenario: dict,
    engine: Engine,
    voice: Voice | None,
    intake: IntakeManager,
    *,
    render_audio: bool = False,
) -> dict:
    """Run a single scenario end-to-end. Returns timing info.

    `render_audio` defaults False because what we mostly care about for
    evaluation is the *script text* — we can read 100 scripts much faster
    than we can listen to 100 audio sessions. Set True for the small
    handful of scenarios we actually want to hear.
    """
    sid = scenario["id"]
    out_dir = OUT_DIR / sid
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "scenario.json").write_text(json.dumps(scenario, indent=2), encoding="utf-8")

    timing = {}

    # Intake: one user message + skip-to-start.
    print(f"  intake ...", flush=True)
    t0 = time.time()
    session = intake.start()
    intake.turn(session.id, scenario["prompt"])
    response, ready = intake.turn(session.id, "just start now")
    if not ready:
        response, ready = intake.turn(session.id, "start")
    timing["intake_s"] = round(time.time() - t0, 1)
    print(f"    {timing['intake_s']}s  ready={ready}", flush=True)

    transcript_lines = []
    for m in session.messages:
        who = "USER" if m["role"] == "user" else "ENGINE"
        transcript_lines.append(f"[{who}]\n{m['content'].strip()}\n")
    (out_dir / "intake.txt").write_text("\n".join(transcript_lines), encoding="utf-8")

    # Generate the session script. Always.
    print(f"  script ...", flush=True)
    t0 = time.time()
    script = generate_session(engine, session.messages)
    timing["script_s"] = round(time.time() - t0, 1)
    words = len(script.split())
    print(f"    {timing['script_s']}s  {words} words", flush=True)
    (out_dir / "script.txt").write_text(script, encoding="utf-8")

    # Render audio only if requested — saves ~30s per scenario.
    if render_audio and voice is not None:
        print(f"  audio  ...", flush=True)
        t0 = time.time()
        wav_bytes = voice.render_session(script)
        timing["audio_s"] = round(time.time() - t0, 1)
        timing["audio_kb"] = round(len(wav_bytes) / 1024, 1)
        print(f"    {timing['audio_s']}s  {timing['audio_kb']} KB", flush=True)
        (out_dir / "session.wav").write_bytes(wav_bytes)
    else:
        timing["audio_s"] = 0

    timing["total_s"] = round(timing["intake_s"] + timing["script_s"] + timing["audio_s"], 1)
    timing["script_words"] = words
    (out_dir / "timing.json").write_text(json.dumps(timing, indent=2), encoding="utf-8")
    return timing


def write_index(results: list[dict]) -> None:
    """Drop an index.md so Sonali can scroll a list of all runs."""
    lines = [
        "# Scenario test results",
        "",
        f"Ran {len(results)} scenarios. Audio + script per scenario in the matching folder.",
        "",
        "| id | total | words | notes | listen |",
        "|---|---|---|---|---|",
    ]
    for r in results:
        s = r["scenario"]
        t = r["timing"]
        lines.append(
            f"| `{s['id']}` | {t.get('total_s', '?')}s | {t.get('script_words', '?')} "
            f"| {s['notes']} | [{s['id']}/session.wav]({s['id']}/session.wav) |"
        )
    (OUT_DIR / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    global OUT_DIR
    p = argparse.ArgumentParser()
    p.add_argument("--only", default=None,
                   help="comma-separated scenario ids to run (default: all)")
    p.add_argument("--from", dest="start_from", type=int, default=0,
                   help="skip the first N scenarios (for resuming a partial run)")
    p.add_argument("--out-dir", default=None,
                   help="output directory (default: logs/scenario-tests/); "
                        "use a different dir for A/B-ing prompt versions")
    p.add_argument("--model", default=None,
                   help="HF model id to load (default: config.model_id); "
                        "use to A/B a different model against the baseline")
    p.add_argument("--no-voice", action="store_true",
                   help="skip loading the TTS voice (we don't render audio in "
                        "text-only eval runs; saves memory + load time)")
    p.add_argument("--verbose", action="store_true",
                   help="INFO logging — shows intake classification + whether a "
                        "scene bible was bound per scenario")
    args = p.parse_args()
    if args.out_dir:
        OUT_DIR = Path(args.out_dir)

    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING)

    scenarios = list(SCENARIOS)
    if args.only:
        wanted = {s.strip() for s in args.only.split(",")}
        scenarios = [s for s in scenarios if s["id"] in wanted]
        missing = wanted - {s["id"] for s in SCENARIOS}
        if missing:
            print(f"[warn] unknown ids: {sorted(missing)}", file=sys.stderr)
    if args.start_from:
        scenarios = scenarios[args.start_from:]

    if not scenarios:
        print("no scenarios to run.")
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"output: {OUT_DIR}")
    print(f"loading engine{'' if args.no_voice else ' + voice'} (one-time) ...")
    if args.model:
        print(f"  model: {args.model}")
    t0 = time.time()
    engine = Engine.load(args.model)
    if args.no_voice:
        voice = None
    else:
        from imagination_engine.tts import Voice  # lazy: only when rendering audio
        voice = Voice.load()
    intake_manager = IntakeManager(engine)
    print(f"  {round(time.time() - t0, 1)}s\n")

    print(f"running {len(scenarios)} scenarios:\n")
    results = []
    for i, scenario in enumerate(scenarios, 1):
        print(f"[{i}/{len(scenarios)}] {scenario['id']} — {scenario['notes']}")
        try:
            timing = run_one(scenario, engine, voice, intake_manager)
            results.append({"scenario": scenario, "timing": timing})
            print(f"    total: {timing['total_s']}s\n", flush=True)
        except Exception as e:
            print(f"  FAILED: {e}\n", flush=True)
            results.append({"scenario": scenario, "timing": {"error": str(e)}})

    write_index(results)
    print(f"\nIndex written: {OUT_DIR / 'index.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
