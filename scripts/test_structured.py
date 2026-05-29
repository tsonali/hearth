"""Tests for the framework's robust structured-output primitive.

Plain-assert script (no pytest dependency). Run:
    .venv/bin/python scripts/test_structured.py

Covers the five failure modes observed in real runs (see structured.py docstring).
Fast, deterministic, no model / no GPU.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from imagination_engine.structured import (  # noqa: E402
    extract_array,
    extract_object,
    extract_json,
    StructuredParseError,
)

CASES_OBJECT = [
    ("clean", '{"a": 1, "b": "two"}', {"a": 1, "b": "two"}),
    ("code fence", '```json\n{"a": 1, "b": "two"}\n```', {"a": 1, "b": "two"}),
    ("prose preamble/postamble",
     'Here is the JSON you asked for:\n{"a": 1, "b": "two"}\nHope that helps!',
     {"a": 1, "b": "two"}),
    ("trailing comma", '{"a": 1, "b": "two",}', {"a": 1, "b": "two"}),
    # raw newline inside a string value — the "Invalid control character" failure
    ("raw newline in string",
     '{"scene": "a quiet room\nwith cold light", "n": 3}',
     {"scene": "a quiet room\nwith cold light", "n": 3}),
    # truncated mid-object (model hit token cap before closing)
    ("truncated object",
     '{"direction": "case_a", "subject": "self with a different person',
     None),  # recovery: parses to a dict, subject value preserved (possibly partial)
]

CASES_ARRAY = [
    ("clean array", '["one", "two", "three"]', ["one", "two", "three"]),
    ("fenced array", '```json\n["one", "two"]\n```', ["one", "two"]),
    # truncated array — the "salvaged unclosed JSON array" generator case
    ("truncated array",
     '["the silence in the wings", "the weight of the mic", "the smell of stage',
     None),  # recovery: returns the complete leading elements
]


def run() -> int:
    failures = 0

    print("== object cases ==")
    for name, raw, expected in CASES_OBJECT:
        try:
            got = extract_object(raw)
            if expected is not None:
                ok = got == expected
            else:
                ok = isinstance(got, dict) and len(got) >= 1  # recovered *something* valid
            print(f"  [{'ok' if ok else 'FAIL'}] {name}: {got}")
            failures += 0 if ok else 1
        except StructuredParseError as e:
            print(f"  [FAIL] {name}: raised {e}")
            failures += 1

    print("== array cases ==")
    for name, raw, expected in CASES_ARRAY:
        try:
            got = extract_array(raw)
            if expected is not None:
                ok = got == expected
            else:
                ok = isinstance(got, list) and len(got) >= 2  # kept the complete elements
            print(f"  [{'ok' if ok else 'FAIL'}] {name}: {got}")
            failures += 0 if ok else 1
        except StructuredParseError as e:
            print(f"  [FAIL] {name}: raised {e}")
            failures += 1

    print("== error case (genuinely unrecoverable) ==")
    try:
        extract_object("there is no json here at all, just prose")
        print("  [FAIL] expected StructuredParseError, got a result")
        failures += 1
    except StructuredParseError:
        print("  [ok] raised StructuredParseError on prose-only input")

    print(f"\n{'ALL PASS' if failures == 0 else f'{failures} FAILURE(S)'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(run())
