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
from imagination_engine.inference import Engine
from imagination_engine.tts import Voice

log = logging.getLogger("imagination_engine")

WEB_DIR = Path(__file__).resolve().parent / "web"

app = FastAPI(title="Imagination Engine", docs_url=None, redoc_url=None)

_engine: Engine | None = None
_voice: Voice | None = None


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


app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


def run(host: str = config.host, port: int = config.port) -> None:
    import uvicorn

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    log.info("Imagination Engine starting on http://%s:%d", host, port)
    uvicorn.run(app, host=host, port=port, log_level="info")
