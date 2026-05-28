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
    RECORDINGS_DIR,
    RECORDING_SCRIPT,
    SPEAKERS_REGISTRY,
)
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
def index() -> HTMLResponse:
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
def intake_start() -> JSONResponse:
    session = get_intake_manager().start()
    return JSONResponse({"session_id": session.id})


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
        log.info("Generating session for %s (voice=%s) ...", session_id, voice)
        script = generate_session(get_engine(), session.messages, on_progress=update)
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


app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


def run(host: str = config.host, port: int = config.port) -> None:
    import uvicorn

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    log.info("Imagination Engine starting on http://%s:%d", host, port)
    uvicorn.run(app, host=host, port=port, log_level="info")
