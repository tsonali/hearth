"""FastAPI server — the v0 'bare text box' shell from build-plan/01.

Bound to 127.0.0.1 only. The product is local-first; the server must never
be reachable from outside this machine.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterator

from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from imagination_engine.config import config
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


app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


def run(host: str = config.host, port: int = config.port) -> None:
    import uvicorn

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    log.info("Imagination Engine starting on http://%s:%d", host, port)
    uvicorn.run(app, host=host, port=port, log_level="info")
