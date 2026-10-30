"""Usage limits: per-device windows plus a global daily cap, in memory.

The device is the random id the student app keeps on the phone (header
X-ZenAI-Device), falling back to the IP address. This is a speed bump against
someone hammering a shared link, not an authentication system.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

LOCAL = {"127.0.0.1", "::1", "localhost", "testclient"}
# A tunnel (cloudflared) connects from this machine, so a request that came
# through it looks local unless the proxy headers are checked too.
PROXY_HEADERS = ("cf-connecting-ip", "x-forwarded-for", "forwarded", "x-real-ip")
_lock = threading.Lock()
_hits: dict = defaultdict(deque)          # (bucket, device) -> timestamps
_global = {"day": "", "n": 0}

PAUSE = ("ZenAI is taking a short pause because a lot of messages came in at once. "
         "Try again in a few minutes. If you need someone right now, call or text 988.")


def is_local(req: Request) -> bool:
    """True only for a request made on this machine, not one relayed by a tunnel."""
    host = req.client.host if req.client else ""
    return host in LOCAL and not any(req.headers.get(h) for h in PROXY_HEADERS)


def client_ip(req: Request) -> str:
    host = req.client.host if req.client else "unknown"
    if host in LOCAL:                      # behind our own tunnel: trust what it says
        fwd = req.headers.get("cf-connecting-ip") or (req.headers.get("x-forwarded-for") or "").split(",")[0]
        return fwd.strip() or host
    return host


def device(req: Request) -> str:
    d = (req.headers.get("x-zenai-device") or "").strip()[:64]
    return d or f"ip:{client_ip(req)}"


def check_code(req: Request) -> None:
    from zenai.config import settings

    if settings.ACCESS_CODE and (req.headers.get("x-zenai-code") or "").strip().upper() != settings.ACCESS_CODE.upper():
        raise HTTPException(401, {"code_required": True, "message": "Enter the class code to use ZenAI."})


def allow(req: Request, bucket: str = "chat") -> bool:
    """True if this device may make one more `bucket` request now (and count it)."""
    from zenai.config import settings

    now, dev = time.time(), device(req)
    rules = ([(600, settings.LIMIT_PER_10MIN), (86400, settings.LIMIT_PER_DAY)] if bucket == "chat"
             else [(600, settings.LIMIT_TTS_PER_10MIN)])
    with _lock:
        q = _hits[(bucket, dev)]
        while q and now - q[0] > 86400:
            q.popleft()
        for window, cap in rules:
            if sum(1 for t in q if now - t <= window) >= cap:
                return False
        if bucket == "chat":
            day = time.strftime("%Y-%m-%d")
            if _global["day"] != day:
                _global.update(day=day, n=0)
            if _global["n"] >= settings.LIMIT_GLOBAL_DAY:
                return False
            _global["n"] += 1
        q.append(now)
        return True


def reset() -> None:
    with _lock:
        _hits.clear()
        _global.update(day="", n=0)
