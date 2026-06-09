"""FastAPI server — the v0 'bare text box' shell from build-plan/01.

Bound to 127.0.0.1 only. The product is local-first; the server must never
be reachable from outside this machine.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Iterator

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from imagination_engine.config import (
    config,
    MEMORY_DB,
    PROJECT_ROOT,
    RECORDINGS_DIR,
    RECORDING_SCRIPT,
    SPEAKERS_REGISTRY,
    SYSTEM_VOICES_DIR,
)
from imagination_engine.audio import persist_session_audio, session_mp3_path
from imagination_engine.generator import generate_session
from imagination_engine.inference import Engine
from imagination_engine.intake import IntakeManager
from imagination_engine.memory import MemoryStore
from imagination_engine.tts import Voice, make_voice

log = logging.getLogger("imagination_engine")

WEB_DIR = Path(__file__).resolve().parent / "web"

app = FastAPI(title="Imagination Engine", docs_url=None, redoc_url=None)

_engine: Engine | None = None
_voices: dict[str, object] = {}
_intake_manager: IntakeManager | None = None
_memory: MemoryStore | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        log.info("Loading model %s ...", config.model_id)
        _engine = Engine.load()
        log.info("Model loaded.")
    return _engine


def get_voice(backend: str = "kokoro"):
    """Return a cached voice instance for the given backend ("kokoro" or "f5")."""
    b = backend.lower().strip()
    if b not in _voices:
        log.info("Loading voice backend: %s", b)
        _voices[b] = make_voice(b)
        log.info("Voice backend ready: %s", b)
    return _voices[b]


def get_memory() -> MemoryStore:
    global _memory
    if _memory is None:
        _memory = MemoryStore(MEMORY_DB)
        log.info("Memory store ready at %s (%d sessions on disk)",
                 MEMORY_DB, _memory.count())
    return _memory


def get_intake_manager() -> IntakeManager:
    global _intake_manager
    if _intake_manager is None:
        _intake_manager = IntakeManager(get_engine(), memory=get_memory())
    return _intake_manager


class GenerateRequest(BaseModel):
    prompt: str
    max_tokens: int | None = None


class SpeakRequest(BaseModel):
    text: str
    speed: float | None = None


@app.get("/", response_class=HTMLResponse)
def home() -> HTMLResponse:
    """Hearth hub — the front door presenting the whole suite (all four tools).

    Replaces the old single-tool 'Imagination Engine' welcome. Routes the user to
    /intake (imagination), /companion, /ask, and (soon) build-your-own.
    See `web/hearth.html`. Old welcome.html kept at /welcome for reference.
    """
    return HTMLResponse((WEB_DIR / "hearth.html").read_text(encoding="utf-8"))


@app.get("/welcome", response_class=HTMLResponse)
def welcome() -> HTMLResponse:
    """The original single-tool welcome page (kept for reference)."""
    return HTMLResponse((WEB_DIR / "welcome.html").read_text(encoding="utf-8"))


@app.get("/welcome/state")
def welcome_state() -> JSONResponse:
    """Lightweight signal for the welcome page to adapt its copy.

    Currently just the number of completed sessions — a returning user
    sees "Begin another session" instead of "Begin your first session".
    Kept deliberately small so this stays a single non-blocking fetch.
    """
    try:
        n = get_memory().count()
    except Exception:
        n = 0
    return JSONResponse({"session_count": n})


def _has_own_voice() -> bool:
    """True iff the user's own F5-fine-tuned voice is usable.

    Requires both the trained checkpoint and the reference clip on disk.
    Used by /voices/options so the intake voice picker only surfaces the
    "Your own voice" card when there's actually one ready to use.
    """
    try:
        # Mirror F5Voice.load()'s file checks but without importing torch/F5
        # — this runs on every welcome page load and must stay cheap.
        from importlib.resources import files as _files
        spk = config.f5_speaker
        ckpt = Path(str(_files("f5_tts").joinpath(
            f"../../ckpts/{spk}/{config.f5_checkpoint}"
        ))).resolve()
        ref_file = PROJECT_ROOT / "data" / "dataset" / spk / "wavs" / f"{config.f5_ref_id}.wav"
        return ckpt.is_file() and ref_file.is_file()
    except Exception:
        return False


def _system_voice_available(name: str) -> bool:
    """True iff the reference clip for the given system voice exists on disk."""
    return (SYSTEM_VOICES_DIR / f"{name}.wav").is_file()


@app.get("/voices/options")
def voices_options() -> JSONResponse:
    """Which voices the intake picker should offer.

    Cheap on-disk file checks — no model loading. Called once on intake
    page load to decide whether to show 2 or 3 voice cards.
    """
    own = _has_own_voice()
    return JSONResponse({
        "her": {
            "available": _system_voice_available("her"),
            "label": "Her",
            "description": "A warm, unhurried woman.",
            "wait": "About 4 minutes wait",
        },
        "him": {
            "available": _system_voice_available("him"),
            "label": "Him",
            "description": "A slow, measured man.",
            "wait": "About 4 minutes wait",
        },
        "own": {
            "available": own,
            "label": "Your own voice",
            "description": "Your voice, trained from your recordings." if own else
                           "Record on /record to train this. About 30 min + overnight.",
            "wait": "About 20 minutes wait" if own else "",
        },
    })


@app.get("/dev", response_class=HTMLResponse)
def dev_engine() -> HTMLResponse:
    """The bare /generate + /speak engine — developer surface, not for end users.

    Useful for sanity-checking the model and TTS without running through the
    full intake → session flow. Kept reachable but moved off /.
    """
    return HTMLResponse((WEB_DIR / "index.html").read_text(encoding="utf-8"))


@app.post("/generate")
def generate(req: GenerateRequest) -> StreamingResponse:
    engine = get_engine()

    def stream() -> Iterator[bytes]:
        for chunk in engine.stream(req.prompt, max_tokens=req.max_tokens):
            yield chunk.encode("utf-8")

    return StreamingResponse(stream(), media_type="text/plain; charset=utf-8")


@app.post("/speak")
def speak(req: SpeakRequest) -> Response:
    # /speak is the "read aloud" surface on the bare engine page — fast voice always.
    voice = get_voice("kokoro")
    wav_bytes = voice.speak(req.text, speed=req.speed)
    return Response(content=wav_bytes, media_type="audio/wav")


# ---------------------------------------------------------------------------
# Recording app — collects Sonali's voice for F5-TTS fine-tuning.
# ---------------------------------------------------------------------------


@app.get("/record", response_class=HTMLResponse)
def record_page() -> HTMLResponse:
    return HTMLResponse((WEB_DIR / "record.html").read_text(encoding="utf-8"))


def _load_speakers() -> dict:
    if not SPEAKERS_REGISTRY.exists():
        raise HTTPException(status_code=500, detail="speakers.json not found")
    return json.loads(SPEAKERS_REGISTRY.read_text(encoding="utf-8"))


def _valid_speaker_ids() -> set[str]:
    return {s["id"] for s in _load_speakers()["speakers"]}


def _speaker_dir(speaker_id: str) -> Path:
    if speaker_id not in _valid_speaker_ids():
        raise HTTPException(status_code=400, detail=f"unknown speaker: {speaker_id}")
    p = RECORDINGS_DIR / speaker_id
    p.mkdir(parents=True, exist_ok=True)
    return p


@app.get("/record/speakers")
def record_speakers() -> JSONResponse:
    return JSONResponse(_load_speakers())


@app.get("/record/sentences")
def record_sentences() -> JSONResponse:
    if not RECORDING_SCRIPT.exists():
        raise HTTPException(status_code=500, detail="recording-script.json not found")
    return JSONResponse(json.loads(RECORDING_SCRIPT.read_text(encoding="utf-8")))


@app.get("/record/progress/{speaker_id}")
def record_progress(speaker_id: str) -> JSONResponse:
    speaker_dir = _speaker_dir(speaker_id)
    done = sorted(p.stem for p in speaker_dir.glob("*.wav"))
    return JSONResponse({"speaker": speaker_id, "completed": done, "count": len(done)})


@app.post("/record/save/{speaker_id}/{sentence_id}")
async def record_save(speaker_id: str, sentence_id: str, request: Request) -> JSONResponse:
    speaker_dir = _speaker_dir(speaker_id)

    script = json.loads(RECORDING_SCRIPT.read_text(encoding="utf-8"))
    valid_ids = {s["id"] for s in script["sentences"]}
    if sentence_id not in valid_ids:
        raise HTTPException(status_code=400, detail=f"unknown sentence id: {sentence_id}")

    body = await request.body()
    if len(body) < 200:
        raise HTTPException(status_code=400, detail="audio too short")

    out_path = speaker_dir / f"{sentence_id}.wav"
    out_path.write_bytes(body)
    log.info("Saved recording: %s (%.1f KB)", out_path, len(body) / 1024)
    return JSONResponse({"saved": sentence_id, "speaker": speaker_id, "bytes": len(body)})


@app.delete("/record/save/{speaker_id}/{sentence_id}")
def record_delete(speaker_id: str, sentence_id: str) -> JSONResponse:
    speaker_dir = _speaker_dir(speaker_id)
    out_path = speaker_dir / f"{sentence_id}.wav"
    if out_path.exists():
        out_path.unlink()
        log.info("Deleted recording: %s", out_path)
        return JSONResponse({"deleted": sentence_id, "speaker": speaker_id})
    raise HTTPException(status_code=404, detail="not found")


# ---------------------------------------------------------------------------
# Intake conversation — Task 02. The doorway into a session.
# ---------------------------------------------------------------------------


class IntakeTurnRequest(BaseModel):
    session_id: str
    message: str


@app.get("/intake", response_class=HTMLResponse)
def intake_page() -> HTMLResponse:
    return HTMLResponse((WEB_DIR / "intake.html").read_text(encoding="utf-8"))


@app.post("/intake/start")
def intake_start(protocol: str = "immersion") -> JSONResponse:
    """Start an intake. `protocol` is the user-facing fork:
    "immersion" (take me somewhere) | "settling" (help me settle / sleep)."""
    session = get_intake_manager().start(protocol=protocol)
    return JSONResponse({"session_id": session.id, "protocol": session.protocol})


@app.post("/intake/turn")
def intake_turn(req: IntakeTurnRequest) -> JSONResponse:
    try:
        response, ready = get_intake_manager().turn(req.session_id, req.message)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return JSONResponse({"response": response, "ready": ready})


@app.get("/intake/{session_id}")
def intake_get(session_id: str) -> JSONResponse:
    try:
        session = get_intake_manager().get(session_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return JSONResponse(session.to_dict())


def _make_progress_updater(session):
    """Return a callback that mutates `session.progress` in place.

    Generator and TTS each accept `on_progress=...`; we wire both into the
    same updater so the user-visible preparing line tells a single coherent
    story: writing 1/3 → 2/3 → 3/3 → rendering 1/N → ... → done.
    """
    def update(*, stage: str, detail: str, step: int = 0, total: int = 0,
               eta_seconds: float | None = None) -> None:
        p = session.progress
        # New stage → reset the started_at clock so elapsed is per-stage.
        if stage != p.stage:
            p.started_at = time.time()
        p.stage = stage
        p.detail = detail
        p.step = step
        p.total = total
        p.eta_seconds = eta_seconds
        p.error = None
    return update


@app.post("/intake/{session_id}/generate")
async def intake_generate(session_id: str, voice: str = "kokoro") -> Response:
    """Run the full intake → script → audio pipeline and return the WAV.

    Query param `voice` picks the backend:
      voice=kokoro  →  fast generic placeholder voice (~3-4 min audio render)
      voice=f5      →  the user's own fine-tuned voice (~15-25 min audio render)

    The generated script text itself is NEVER returned over the wire —
    per [[project-voice-design]] it stays as the hidden thinking layer.
    The user hears the audio; that's the only delivery surface.

    The heavy work runs in a threadpool so other handlers — notably the
    /status endpoint the client polls every 2 seconds — stay responsive.
    The session's `progress` field is updated synchronously from inside the
    worker via callbacks; the GET /status handler just reads the dataclass.
    """
    intake = get_intake_manager()
    try:
        session = intake.get(session_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    if not session.ready:
        raise HTTPException(status_code=409, detail="intake not yet finalized")

    update = _make_progress_updater(session)

    def _do_work() -> tuple[bytes, str, object]:
        log.info("Generating session for %s (voice=%s, protocol=%s) ...",
                 session_id, voice, session.protocol)
        script = generate_session(get_engine(), session.messages,
                                  protocol=session.protocol, on_progress=update)
        log.info("Rendering audio for %s (%d-word script, voice=%s) ...",
                 session_id, len(script.split()), voice)
        voice_obj = get_voice(voice)
        wav_bytes = voice_obj.render_session(script, on_progress=update)
        log.info("Session for %s ready (%.1f KB)", session_id, len(wav_bytes) / 1024)
        return wav_bytes, script, voice_obj

    try:
        wav_bytes, script, voice_obj = await run_in_threadpool(_do_work)
    except Exception as e:
        session.progress.stage = "error"
        session.progress.error = str(e)
        session.progress.detail = "Something went wrong while building your session."
        log.exception("generate failed for %s", session_id)
        raise HTTPException(status_code=500, detail=str(e))

    # Done — flip progress to its terminal state so the client can stop polling.
    update(stage="done", detail="Your session is ready.", step=0, total=0, eta_seconds=0)

    # Persist the audio to disk so the user can download an MP3 to save /
    # AirDrop / carry to their phone. WAV is the source-of-truth for
    # inline playback; MP3 is the smaller share artifact.
    try:
        await run_in_threadpool(persist_session_audio, session_id, wav_bytes)
    except Exception as e:
        # Audio download is nice-to-have, not load-bearing — log and
        # continue. The user still gets the inline WAV stream below.
        log.warning("session-audio persist failed for %s: %s", session_id, e)

    # Persist to local memory so future intakes can reference this session.
    try:
        speaker = getattr(voice_obj, "speaker", None)
        get_memory().save_session(
            session_id=session_id,
            intake_transcript=session.messages,
            script=script,
            voice_backend=voice,
            speaker=speaker,
        )
    except Exception as e:
        log.warning("memory save failed for %s: %s", session_id, e)

    return Response(content=wav_bytes, media_type="audio/wav")


@app.get("/intake/{session_id}/download")
def intake_download(session_id: str) -> Response:
    """Return the rendered session as MP3 for download.

    Used by the Save button in the UI. The Content-Disposition header
    triggers a browser download (and on iOS/macOS, makes the file
    available to the Share sheet for AirDrop). Filename includes today's
    date so saved sessions don't collide.
    """
    from datetime import datetime

    mp3_path = session_mp3_path(session_id)
    if not mp3_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="audio not yet rendered for this session",
        )

    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"imagination-engine-{today}-{session_id[:8]}.mp3"
    return Response(
        content=mp3_path.read_bytes(),
        media_type="audio/mpeg",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/intake/{session_id}/status")
def intake_status(session_id: str) -> JSONResponse:
    """Live progress for the client's preparing-state polling loop.

    Cheap read of the in-memory SessionProgress dataclass. The client polls
    this every ~2 seconds while the long generate+render call is in flight.
    """
    try:
        session = get_intake_manager().get(session_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return JSONResponse(session.progress.to_dict())


class ReflectRequest(BaseModel):
    reflection: str


@app.post("/intake/{session_id}/reflect")
def intake_reflect(session_id: str, req: ReflectRequest) -> JSONResponse:
    """Capture the user's post-session reflection. Stored locally only."""
    text = (req.reflection or "").strip()
    if not text:
        return JSONResponse({"saved": False, "reason": "empty"})
    updated = get_memory().capture_reflection(session_id, text)
    if not updated:
        raise HTTPException(status_code=404, detail="session not in memory")
    return JSONResponse({"saved": True})


# ---------------------------------------------------------------------------
# Family C — the honest reflective companion. Conversations held per-session in
# memory; cross-session continuity via CompanionMemory (local SQLite).
# ---------------------------------------------------------------------------
_companions: dict[str, object] = {}
_companion_memory = None


def _get_companion_memory():
    global _companion_memory
    if _companion_memory is None:
        from imagination_engine.companion import CompanionMemory
        _companion_memory = CompanionMemory(MEMORY_DB.parent / "companion.sqlite")
    return _companion_memory


@app.get("/companion", response_class=HTMLResponse)
def companion_page() -> HTMLResponse:
    """The honest reflective companion — chat UI (Family C)."""
    return HTMLResponse((WEB_DIR / "companion.html").read_text(encoding="utf-8"))


class CompanionRequest(BaseModel):
    session_id: str
    message: str


@app.post("/companion/turn")
async def companion_turn(req: CompanionRequest) -> JSONResponse:
    """One turn with the honest reflective companion (Family C)."""
    from imagination_engine.companion import Companion
    comp = _companions.get(req.session_id)
    if comp is None:
        comp = Companion(get_engine(), memory=_get_companion_memory())
        _companions[req.session_id] = comp
    turn = await run_in_threadpool(comp.turn, req.message)
    return JSONResponse({"reply": turn.reply, "flagged": turn.flagged})


# ---------------------------------------------------------------------------
# Family B/D — ask questions grounded in the user's own files. The corpus is
# indexed once (POST /ask/index), then queried (POST /ask/query).
# ---------------------------------------------------------------------------
_docqa = None


def _get_docqa():
    global _docqa
    if _docqa is None:
        from imagination_engine.doc_qa import DocQA
        from imagination_engine.rag import RagStore, MLXEmbedder
        store = RagStore(MEMORY_DB.parent / "ask.sqlite", embedder=MLXEmbedder())
        _docqa = DocQA(get_engine(), store)
    return _docqa


@app.get("/ask", response_class=HTMLResponse)
def ask_page() -> HTMLResponse:
    """Ask questions grounded in your own files — UI (Family B/D)."""
    return HTMLResponse((WEB_DIR / "ask.html").read_text(encoding="utf-8"))


class IndexRequest(BaseModel):
    corpus: str = "default"
    path: str


class AskRequest(BaseModel):
    corpus: str = "default"
    question: str


@app.post("/ask/index")
async def ask_index(req: IndexRequest) -> JSONResponse:
    """Index a file or folder into a named corpus (one-time per corpus)."""
    p = Path(req.path).expanduser()
    if not p.exists():
        raise HTTPException(status_code=400, detail=f"path not found: {p}")
    rep = await run_in_threadpool(_get_docqa().index, req.corpus, p)
    return JSONResponse(rep)


@app.post("/ask/query")
async def ask_query(req: AskRequest) -> JSONResponse:
    """Answer a question grounded ONLY in the indexed files. Refuses if not present."""
    ans = await run_in_threadpool(_get_docqa().ask, req.corpus, req.question)
    return JSONResponse({"answer": ans.text, "sources": ans.sources, "grounded": ans.grounded})


# ---------------------------------------------------------------------------
# Family B — the at-home secretary. Stateless text transforms on the user's own
# words (draft / reply / summarize / rewrite / extract / organize). Streams.
# ---------------------------------------------------------------------------
_assistant = None


def _get_assistant():
    global _assistant
    if _assistant is None:
        from imagination_engine.utility import Assistant
        _assistant = Assistant(get_engine())
    return _assistant


@app.get("/utility", response_class=HTMLResponse)
def utility_page() -> HTMLResponse:
    """The at-home secretary — draft, reply, summarize, rewrite, extract, organize."""
    return HTMLResponse((WEB_DIR / "utility.html").read_text(encoding="utf-8"))


@app.get("/utility/tasks")
def utility_tasks() -> JSONResponse:
    """The task catalog the page renders its selector from."""
    from imagination_engine.utility import task_catalog
    return JSONResponse({"tasks": task_catalog()})


class UtilityRequest(BaseModel):
    task: str
    text: str
    instruction: str = ""
    tone: str = ""
    style_sample: str = ""


@app.post("/utility/run")
def utility_run(req: UtilityRequest) -> StreamingResponse:
    """Run one utility task, streaming the finished artifact back as it's written."""
    assistant = _get_assistant()

    def stream() -> Iterator[bytes]:
        try:
            for chunk in assistant.stream(
                req.task, req.text, instruction=req.instruction,
                tone=req.tone, style_sample=req.style_sample,
            ):
                yield chunk.encode("utf-8")
        except (KeyError, ValueError) as e:
            yield f"[error: {e}]".encode("utf-8")

    return StreamingResponse(stream(), media_type="text/plain; charset=utf-8")


# ---------------------------------------------------------------------------
# Family D — Build Your Own. The user describes a standing instrument (persona +
# optional grounding on their files), keeps it, and returns to it. Registry +
# RAG store live in local SQLite beside the other stores.
# ---------------------------------------------------------------------------
_instrument_registry = None
_open_instruments: dict[str, object] = {}


def _get_instrument_registry():
    global _instrument_registry
    if _instrument_registry is None:
        from imagination_engine.instrument import InstrumentRegistry
        _instrument_registry = InstrumentRegistry(MEMORY_DB.parent / "instruments.sqlite")
    return _instrument_registry


@app.get("/build", response_class=HTMLResponse)
def build_page() -> HTMLResponse:
    """Build Your Own — describe an instrument, keep it, return to it (Family D)."""
    return HTMLResponse((WEB_DIR / "build.html").read_text(encoding="utf-8"))


@app.get("/build/list")
def build_list() -> JSONResponse:
    """The instruments the user has built (for the picker)."""
    specs = _get_instrument_registry().list()
    return JSONResponse({"instruments": [
        {"name": s.name, "grounded": s.grounded, "created": s.created} for s in specs
    ]})


class BuildCreateRequest(BaseModel):
    name: str
    description: str
    files: str = ""   # optional path to ground on


@app.post("/build/create")
async def build_create(req: BuildCreateRequest) -> JSONResponse:
    """Create + persist a new instrument from a description (+ optional folder)."""
    from datetime import datetime
    from imagination_engine.instrument import build_instrument

    name = (req.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="name required")
    if _get_instrument_registry().get(name) is not None:
        raise HTTPException(status_code=409, detail=f"an instrument named {name!r} already exists")
    if not (req.description or "").strip():
        raise HTTPException(status_code=400, detail="description required")

    files_path = None
    if (req.files or "").strip():
        files_path = Path(req.files).expanduser()
        if not files_path.exists():
            raise HTTPException(status_code=400, detail=f"path not found: {files_path}")

    def _do():
        return build_instrument(
            _get_instrument_registry(), name=name, description=req.description,
            created=datetime.now().isoformat(timespec="seconds"), files=files_path,
        )

    spec = await run_in_threadpool(_do)
    _open_instruments.pop(name, None)  # invalidate any cached open instance
    return JSONResponse({"name": spec.name, "grounded": spec.grounded, "created": spec.created})


class BuildAskRequest(BaseModel):
    name: str
    message: str


@app.post("/build/ask")
async def build_ask(req: BuildAskRequest) -> JSONResponse:
    """Talk to a built instrument. Opens (and caches) it, then asks."""
    from imagination_engine.instrument import open_instrument

    inst = _open_instruments.get(req.name)
    if inst is None:
        inst = await run_in_threadpool(
            open_instrument, get_engine(), _get_instrument_registry(), req.name
        )
        if inst is None:
            raise HTTPException(status_code=404, detail=f"no instrument named {req.name!r}")
        _open_instruments[req.name] = inst

    reply = await run_in_threadpool(inst.ask, req.message)
    return JSONResponse({"reply": reply, "grounded": inst.spec.grounded})


app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


def run(host: str = config.host, port: int = config.port) -> None:
    import uvicorn

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    log.info("Imagination Engine starting on http://%s:%d", host, port)
    uvicorn.run(app, host=host, port=port, log_level="info")
