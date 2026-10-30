"""ZenAI's spoken voice: POST /tts turns a reply into natural speech (MP3).

Voice mode used the browser's built-in voices, which sound robotic. This uses a
neural voice (Microsoft's, through edge-tts, no API key) chosen to be calm and
unhurried. Only the reply text is sent to the speech service, never the
student's message. If the service can't be reached the app falls back to the
browser's own voice.
"""

from __future__ import annotations

import hashlib
from collections import OrderedDict

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field

router = APIRouter(tags=["voice"])
_CACHE: OrderedDict = OrderedDict()     # the same reply is often replayed; keep the last 64
_MAX = 64


class SpeakIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=800)


@router.post("/tts")
async def tts(body: SpeakIn, req: Request) -> Response:
    import edge_tts

    from zenai.api import limits
    from zenai.config import settings

    limits.check_code(req)
    if not limits.allow(req, "tts"):
        raise HTTPException(429, {"limited": True, "message": limits.PAUSE})

    key = hashlib.sha1(f"{settings.TTS_VOICE}|{settings.TTS_RATE}|{body.text}".encode()).hexdigest()
    if key in _CACHE:
        _CACHE.move_to_end(key)
        return Response(_CACHE[key], media_type="audio/mpeg")
    try:
        audio = b""
        async for chunk in edge_tts.Communicate(body.text, settings.TTS_VOICE, rate=settings.TTS_RATE).stream():
            if chunk["type"] == "audio":
                audio += chunk["data"]
    except Exception as e:
        raise HTTPException(503, f"speech service unavailable: {e.__class__.__name__}") from e
    if not audio:
        raise HTTPException(503, "speech service returned no audio")
    _CACHE[key] = audio
    if len(_CACHE) > _MAX:
        _CACHE.popitem(last=False)
    return Response(audio, media_type="audio/mpeg")


@router.get("/tts/stream")
async def tts_stream(req: Request, text: str = Query(..., min_length=1, max_length=800)) -> Response:
    """The same voice, streamed: the app starts playing at the first chunk
    (about 1.8 s) instead of waiting for the whole clip (about 4 s)."""
    import edge_tts

    from zenai.api import limits
    from zenai.config import settings

    limits.check_code(req)
    if not limits.allow(req, "tts"):
        raise HTTPException(429, {"limited": True, "message": limits.PAUSE})

    key = hashlib.sha1(f"{settings.TTS_VOICE}|{settings.TTS_RATE}|{text}".encode()).hexdigest()
    if key in _CACHE:
        _CACHE.move_to_end(key)
        return Response(_CACHE[key], media_type="audio/mpeg")

    async def gen():
        got = b""
        try:
            async for chunk in edge_tts.Communicate(text, settings.TTS_VOICE, rate=settings.TTS_RATE).stream():
                if chunk["type"] == "audio":
                    got += chunk["data"]
                    yield chunk["data"]
        except Exception:  # noqa: BLE001 -- a cut stream ends the clip; the app falls back if nothing came
            return
        if got:
            _CACHE[key] = got
            if len(_CACHE) > _MAX:
                _CACHE.popitem(last=False)

    return StreamingResponse(gen(), media_type="audio/mpeg", headers={"Cache-Control": "no-store"})
