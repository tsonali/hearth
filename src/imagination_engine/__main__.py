"""CLI entry: `python -m imagination_engine` or `imagination-engine`.

Subcommands:
    serve  (default) Run the local FastAPI server on loopback.
    probe  One-shot inference smoke test from the command line.
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
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
