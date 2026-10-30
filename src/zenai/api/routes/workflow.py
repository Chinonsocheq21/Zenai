"""Live pipeline events for the workflow viewer at /workflow/.

GET /workflow/events?since=N  Server-Sent Events: every stage of every turn as it
                              happens. Redacted text only, from memory only.

Both are for the presenter's laptop only. Through the class tunnel they are
refused, so nobody with the link can watch other students' messages.
"""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from zenai.api import limits

router = APIRouter(tags=["workflow"])


def _local(req: Request) -> None:
    if not limits.is_local(req):
        raise HTTPException(403, "The workflow viewer only works on the presenter's laptop.")


@router.get("/workflow/events")
async def stream(req: Request, since: int = 0) -> StreamingResponse:
    from zenai import events

    _local(req)

    async def gen():
        seq, idle = since, 0
        yield "retry: 1500\n\n"
        while True:
            batch = events.since(seq)
            for e in batch:
                seq = e["seq"]
                yield f"id: {seq}\ndata: {json.dumps(e)}\n\n"
            idle = 0 if batch else idle + 1
            if idle and idle % 100 == 0:   # ~every 15 s
                yield ": keep-alive\n\n"
            await asyncio.sleep(0.15)

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.get("/workflow/recent")
def recent(req: Request, limit: int = 400) -> dict:
    """The recent events, for a viewer that opens after turns have already run."""
    from zenai import events

    _local(req)

    ev = events.since(0)[-limit:]
    return {"events": ev, "last": events.last_seq()}
