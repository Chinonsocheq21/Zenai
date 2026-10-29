"""Live turn events, for the workflow viewer (/workflow/).

Every stage of a turn publishes an event here as it happens, so the viewer can
draw a message moving through the pipeline in real time while a student types
in the app. Testing-phase tooling:

  - in memory only, the last 2,000 events; nothing is written to disk;
  - only REDACTED text is ever published, never the student's raw message;
  - switched off with WORKFLOW_EVENTS=false (do that before real students).
"""

from __future__ import annotations

import threading
import time
from collections import deque

_buf: deque = deque(maxlen=2000)
_lock = threading.Lock()
_seq = 0


def publish(turn: str, type_: str, **data) -> None:
    from zenai.config import settings

    if not settings.WORKFLOW_EVENTS:
        return
    global _seq
    with _lock:
        _seq += 1
        _buf.append({"seq": _seq, "turn": turn, "type": type_, "t": round(time.time() * 1000), **data})


def since(seq: int) -> list[dict]:
    with _lock:
        return [e for e in _buf if e["seq"] > seq]


def last_seq() -> int:
    with _lock:
        return _seq
