"""FastAPI server — the v0 'bare text box' shell from build-plan/01.

Bound to 127.0.0.1 only. The product is local-first; the server must never
be reachable from outside this machine.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Iterator

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from imagination_engine.config import (
    config,
    RECORDINGS_DIR,
    RECORDING_SCRIPT,
    SPEAKERS_REGISTRY,
)
from imagination_engine.generator import generate_session
from imagination_engine.inference import Engine
from imagination_engine.intake import IntakeManager
from imagination_engine.tts import Voice

log = logging.getLogger("imagination_engine")

WEB_DIR = Path(__file__).resolve().parent / "web"

app = FastAPI(title="Imagination Engine", docs_url=None, redoc_url=None)

_engine: Engine | None = None
_voice: Voice | None = None
_intake_manager: IntakeManager | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        log.info("Loading model %s ...", config.model_id)
        _engine = Engine.load()
        log.info("Model loaded.")
    return _engine


def get_voice() -> Voice:
    global _voice
    if _voice is None:
        log.info("Loading TTS voice (%s) ...", config.tts_voice)
        _voice = Voice.load()
        log.info("Voice loaded.")
    return _voice


def get_intake_manager() -> IntakeManager:
    global _intake_manager
    if _intake_manager is None:
        _intake_manager = IntakeManager(get_engine())
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
    voice = get_voice()
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


@app.post("/intake/{session_id}/generate")
def intake_generate(session_id: str) -> Response:
    """Run the full intake → script → audio pipeline and return the WAV.

    This is the cool-experience endpoint. Heavy: ~60-90 seconds on M3
    (model generation + per-paragraph TTS render). The client shows a
    "preparing" state during the wait.

    The generated script text itself is NEVER returned over the wire —
    per [[project-voice-design]] it stays as the hidden thinking layer.
    The user hears the audio; that's the only delivery surface.
    """
    intake = get_intake_manager()
    try:
        session = intake.get(session_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    if not session.ready:
        raise HTTPException(status_code=409, detail="intake not yet finalized")

    log.info("Generating session for %s ...", session_id)
    script = generate_session(get_engine(), session.messages)
    log.info("Rendering audio for %s (%d-word script) ...", session_id, len(script.split()))
    wav_bytes = get_voice().render_session(script)
    log.info("Session for %s ready (%.1f KB)", session_id, len(wav_bytes) / 1024)
    return Response(content=wav_bytes, media_type="audio/wav")


app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


def run(host: str = config.host, port: int = config.port) -> None:
    import uvicorn

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    log.info("Imagination Engine starting on http://%s:%d", host, port)
    uvicorn.run(app, host=host, port=port, log_level="info")
