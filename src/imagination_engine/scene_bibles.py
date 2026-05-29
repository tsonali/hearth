"""Scene bibles — load hand-curated archetype canvases from YAML.

A scene bible is a rich, human-authored description of one archetype of
imagining (backstage-pre-show, romantic-intimate, retire-young, etc.)
that the engine generates against. See `data/scene_bibles/README.md` for
the rationale and format.

This module just loads the YAML files. Matching user intake to an
archetype is the classifier's job (see `comprehension.py`); generating
the script using a bible is the generator's job (see `generator.py`).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

# We use PyYAML — already an indirect dep of several packages we install.
# If it's not present, scene-bible support falls back to off.
try:
    import yaml
    HAVE_YAML = True
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore
    HAVE_YAML = False

from imagination_engine.config import DATA_DIR

log = logging.getLogger(__name__)

BIBLES_DIR = DATA_DIR / "scene_bibles"


@dataclass
class Beat:
    """One dramatic beat — a moment within the scene."""
    description: str
    function: str = ""


@dataclass
class Scene:
    """The where/when/who_else/mood of the scene."""
    where: str = ""
    when: str = ""
    who_else: str = ""
    mood: str = ""

    def to_brief(self) -> str:
        """Render as a brief prose block for inclusion in generation prompts."""
        parts = []
        if self.where:
            parts.append(f"WHERE: {self.where}")
        if self.when:
            parts.append(f"WHEN: {self.when}")
        if self.who_else:
            parts.append(f"WHO ELSE IS PRESENT: {self.who_else}")
        if self.mood:
            parts.append(f"MOOD: {self.mood}")
        return "\n".join(parts)


@dataclass
class SceneBible:
    """One hand-curated archetype canvas."""
    archetype: str
    trigger_phrases: list[str] = field(default_factory=list)
    direction: str = "case_a"  # case_a | case_b | case_c
    scene: Scene = field(default_factory=Scene)
    anchors: list[str] = field(default_factory=list)
    beats: list[Beat] = field(default_factory=list)
    forbidden_specifics: list[str] = field(default_factory=list)
    style_notes: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> "SceneBible":
        scene_d = d.get("scene", {}) or {}
        beats_raw = d.get("beats", []) or []
        beats = [
            Beat(description=b.get("description", ""), function=b.get("function", ""))
            for b in beats_raw if isinstance(b, dict)
        ]
        return cls(
            archetype=d.get("archetype", ""),
            trigger_phrases=list(d.get("trigger_phrases", []) or []),
            direction=d.get("direction", "case_a"),
            scene=Scene(
                where=scene_d.get("where", ""),
                when=scene_d.get("when", ""),
                who_else=scene_d.get("who_else", ""),
                mood=scene_d.get("mood", ""),
            ),
            anchors=list(d.get("anchors", []) or []),
            beats=beats,
            forbidden_specifics=list(d.get("forbidden_specifics", []) or []),
            style_notes=list(d.get("style_notes", []) or []),
        )

    def context_block(self) -> str:
        """A prose block describing this scene bible — injected into generation prompts.

        Goes after the classifier's direction block. Tells the generator
        what scene to produce, with concrete anchors to hit and style
        notes to obey.
        """
        parts = []
        parts.append(f"SCENE ARCHETYPE: {self.archetype}")
        if self.scene.to_brief():
            parts.append("\n" + self.scene.to_brief())
        if self.anchors:
            parts.append("\nSENSORY ANCHORS — the body of the script should hit these:")
            for a in self.anchors:
                parts.append(f"  - {a}")
        if self.style_notes:
            parts.append("\nSTYLE NOTES for this archetype:")
            for s in self.style_notes:
                parts.append(f"  - {s}")
        if self.forbidden_specifics:
            parts.append("\nFORBIDDEN for this archetype:")
            for f in self.forbidden_specifics:
                parts.append(f"  - {f}")
        return "\n".join(parts)


@lru_cache(maxsize=1)
def list_bibles() -> dict[str, SceneBible]:
    """Load all .yaml files under data/scene_bibles/ into a dict by archetype name.

    Cached for the process lifetime — bibles don't change at runtime.
    """
    if not HAVE_YAML:
        log.warning("PyYAML not installed; scene-bible support disabled")
        return {}
    if not BIBLES_DIR.is_dir():
        log.info("no data/scene_bibles/ directory; scene-bible support disabled")
        return {}

    out: dict[str, SceneBible] = {}
    for path in sorted(BIBLES_DIR.glob("*.yaml")):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                log.warning("skipping %s — not a YAML mapping", path.name)
                continue
            bible = SceneBible.from_dict(data)
            if not bible.archetype:
                log.warning("skipping %s — no archetype field", path.name)
                continue
            out[bible.archetype] = bible
        except Exception as e:
            log.warning("skipping %s — load error: %s", path.name, e)
    log.info("loaded %d scene bibles: %s", len(out), sorted(out.keys()))
    return out


def get_bible(archetype: str) -> SceneBible | None:
    """Look up a scene bible by archetype name. Returns None if not found."""
    return list_bibles().get(archetype)


def archetype_names() -> list[str]:
    """All loaded archetype names, sorted."""
    return sorted(list_bibles().keys())


def trigger_phrase_index() -> list[tuple[str, str]]:
    """Flat list of (trigger_phrase, archetype) for fuzzy matching at intake time."""
    out = []
    for arch, bible in list_bibles().items():
        for phrase in bible.trigger_phrases:
            out.append((phrase, arch))
    return out
