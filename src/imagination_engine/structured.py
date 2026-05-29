"""Robust structured-output parsing — a FRAMEWORK-GENERAL reliability primitive.

This is part of the framework, not the guided-imagination task. Any task plugged
into the engine that needs structured output (JSON) from a small local model
relies on this. It is task-agnostic on purpose: guided imagination is just the
first task that uses it.

WHY THIS EXISTS. The 2026-05-29 model bake-off found that the unreliability of
small local models is a *scaffolding* problem, not a model problem — every
candidate (Llama, NeMo, Qwen) still produced JSON that naive `json.loads` chokes
on. Small models reliably *almost* emit valid JSON. The real-world failure modes,
all observed in our own runs:

  1. wrapped in ```json ... ``` code fences
  2. prefaced/followed by prose ("Here is the JSON: ...")
  3. trailing commas before } or ]
  4. raw newlines / control chars inside string values  (the "Invalid control
     character" classifier failure in logs/v5.2-probe.log)
  5. truncated mid-structure when the model hits the token cap — an unclosed
     array/object/string  (the "salvaged unclosed JSON array" generator warning)

`extract_json` recovers all five deterministically (no model call), so structured
output becomes reliable enough to build on. This replaces the ad-hoc per-call
salvage that used to live in comprehension.py and generator.py.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Literal

log = logging.getLogger(__name__)

Kind = Literal["object", "array"]
_DELIMS = {"object": ("{", "}"), "array": ("[", "]")}


class StructuredParseError(ValueError):
    """Raised when text cannot be recovered into the requested JSON shape."""


def _strip_fences(text: str) -> str:
    """Remove a leading ```json / ``` fence and a trailing ``` fence, plus any
    leading/trailing prose whitespace. Does NOT remove prose around the JSON —
    that's handled by locating the delimiter region in `extract_json`."""
    t = text.strip()
    t = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", t)
    t = re.sub(r"\s*```$", "", t)
    return t.strip()


def _repair(region: str) -> str:
    """Single deterministic pass that fixes the common malformations.

    Walks the text as a tiny state machine tracking string/escape/bracket state:
      - escapes literal control chars (newlines, tabs, …) that appear INSIDE a
        string literal (illegal in JSON, but models emit them constantly),
      - closes an unterminated trailing string,
      - drops trailing commas,
      - closes any still-open brackets/braces at EOF (truncation salvage).
    Applied only as a fallback after a direct parse fails, so well-formed JSON is
    never touched.
    """
    out: list[str] = []
    stack: list[str] = []
    in_str = False
    escaped = False

    for ch in region:
        if escaped:
            out.append(ch)
            escaped = False
            continue
        if ch == "\\":
            out.append(ch)
            escaped = True
            continue
        if in_str:
            if ch == '"':
                in_str = False
                out.append(ch)
            elif ch == "\n":
                out.append("\\n")
            elif ch == "\r":
                out.append("\\r")
            elif ch == "\t":
                out.append("\\t")
            elif ord(ch) < 0x20:
                out.append("\\u%04x" % ord(ch))
            else:
                out.append(ch)
            continue
        # outside a string
        if ch == '"':
            in_str = True
        elif ch in "{[":
            stack.append(ch)
        elif ch in "}]":
            if stack:
                stack.pop()
        out.append(ch)

    if in_str:  # unterminated trailing string
        out.append('"')
    s = "".join(out).rstrip()
    # drop trailing commas (e.g. `"a",` cut off, or `{"a":1,}`)
    s = re.sub(r",\s*$", "", s)
    s = re.sub(r",(\s*[}\]])", r"\1", s)
    # close any brackets the model never closed, innermost first
    while stack:
        opener = stack.pop()
        s += "}" if opener == "{" else "]"
    return s


def extract_json(text: str, kind: Kind = "object") -> Any:
    """Recover a JSON `object` or `array` from a model's raw text output.

    Tries a direct parse of the located region first; only if that fails does it
    apply `_repair` and retry. Raises StructuredParseError if still unrecoverable.
    """
    if not text or not text.strip():
        raise StructuredParseError("empty model output")

    open_ch, close_ch = _DELIMS[kind]
    body = _strip_fences(text)

    start = body.find(open_ch)
    if start == -1:
        raise StructuredParseError(
            f"no {open_ch!r} found in output: {text[:200]!r}"
        )
    end = body.rfind(close_ch)
    region = body[start : end + 1] if end > start else body[start:]

    try:
        return json.loads(region)
    except (json.JSONDecodeError, ValueError):
        pass

    repaired = _repair(region)
    try:
        result = json.loads(repaired)
        log.warning("structured output recovered via repair (kind=%s)", kind)
        return result
    except (json.JSONDecodeError, ValueError) as e:
        raise StructuredParseError(
            f"unrecoverable {kind} (after repair): {e}; raw head={text[:200]!r}"
        ) from e


def extract_object(text: str) -> dict:
    obj = extract_json(text, "object")
    if not isinstance(obj, dict):
        raise StructuredParseError(f"expected object, got {type(obj).__name__}")
    return obj


def extract_array(text: str) -> list:
    arr = extract_json(text, "array")
    if not isinstance(arr, list):
        raise StructuredParseError(f"expected array, got {type(arr).__name__}")
    return arr
