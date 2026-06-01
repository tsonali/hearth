"""CLI entry: `python -m imagination_engine` or `imagination-engine`.

Subcommands:
    serve      (default) Run the local FastAPI server on loopback.
    probe      One-shot inference smoke test from the command line.
    companion  Interactive honest-reflective-companion chat (Family C).
    ask        Q&A grounded in your own files (Family B/D): index a path, then ask.
    imagine    Generate a guided-imagination session from a one-line prompt (Family A).
"""

from __future__ import annotations

import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(prog="imagination-engine")
    sub = parser.add_subparsers(dest="cmd")

    serve = sub.add_parser("serve", help="Run the local server")
    serve.add_argument("--host", default=None)
    serve.add_argument("--port", type=int, default=None)

    probe = sub.add_parser("probe", help="One-shot inference smoke test")
    probe.add_argument(
        "prompt",
        nargs="?",
        default="In one short sentence, say hello.",
    )
    probe.add_argument("--max-tokens", type=int, default=128)

    comp = sub.add_parser("companion", help="Interactive reflective companion (Family C)")

    askp = sub.add_parser("ask", help="Q&A grounded in your own files (Family B/D)")
    askp.add_argument("path", help="file or folder to index + ask about")
    askp.add_argument("question", nargs="?", default=None,
                      help="a question; omit for interactive mode")
    askp.add_argument("--no-semantic", action="store_true",
                      help="use the lexical fallback embedder (no model download)")

    img = sub.add_parser("imagine", help="Generate a guided session (Family A)")
    img.add_argument("prompt", help='what to imagine, e.g. "retiring young by the sea"')

    args = parser.parse_args()
    cmd = args.cmd or "serve"

    if cmd == "serve":
        from imagination_engine.config import config
        from imagination_engine.server import run

        run(
            host=args.host or config.host,
            port=args.port or config.port,
        )
    elif cmd == "probe":
        from imagination_engine.inference import Engine

        engine = Engine.load()
        for chunk in engine.stream(args.prompt, max_tokens=args.max_tokens):
            print(chunk, end="", flush=True)
        print()

    elif cmd == "companion":
        from imagination_engine.companion import Companion
        from imagination_engine.inference import Engine
        print("Honest reflective companion. It's a mirror, not a person. "
              "Type your thoughts; Ctrl-C to leave.\n")
        c = Companion(Engine.load())
        try:
            while True:
                msg = input("you > ").strip()
                if not msg:
                    continue
                turn = c.turn(msg)
                print(f"\n    {turn.reply}\n")
        except (KeyboardInterrupt, EOFError):
            print("\n(closed — nothing was saved or sent anywhere.)")

    elif cmd == "ask":
        from pathlib import Path
        from imagination_engine.doc_qa import DocQA
        qa = DocQA.open(Path.home() / ".cache" / "imagination_engine" / "ask.sqlite",
                        semantic=not args.no_semantic)
        print(f"indexing {args.path} ...")
        rep = qa.index("ask", Path(args.path))
        print(f"  indexed {rep['chunks']} chunks from {rep['files']} file(s).\n")

        def answer(q: str) -> None:
            a = qa.ask("ask", q)
            print(f"\n{a.text}\n" + (f"  [sources: {', '.join(a.sources)}]\n" if a.sources else ""))

        if args.question:
            answer(args.question)
        else:
            print("Ask about your files. Ctrl-C to leave.\n")
            try:
                while True:
                    q = input("ask > ").strip()
                    if q:
                        answer(q)
            except (KeyboardInterrupt, EOFError):
                print("\n(closed.)")

    elif cmd == "imagine":
        from imagination_engine.generator import generate_session
        from imagination_engine.inference import Engine
        transcript = [{"role": "user", "content": args.prompt},
                      {"role": "user", "content": "just start now"}]
        script = generate_session(Engine.load(), transcript)
        print("\n" + script + "\n")

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
