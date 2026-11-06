"""Usage limits: per-device windows plus a global daily cap.

The device is the random id the student app keeps on the phone (header
X-ZenAI-Device), falling back to the IP address. This is a speed bump against
someone hammering a shared link, not an authentication system.

Where the counts live:
  * Redis (Upstash, over its REST API) when KV_REST_API_URL/KV_REST_API_TOKEN
    or UPSTASH_REDIS_REST_URL/UPSTASH_REDIS_REST_TOKEN are set. On Vercel each
    request may run on a different instance, so memory alone would let every
    instance hand out its own allowance.
  * Memory otherwise (the laptop), and ALSO whenever Redis errors or is slow:
    a limit that fails must never stop a student reaching the crisis check.
Device ids are hashed before they become Redis keys.
"""

from __future__ import annotations

import hashlib
import logging
import os
import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

LOCAL = {"127.0.0.1", "::1", "localhost", "testclient"}
# A tunnel (cloudflared) connects from this machine, so a request that came
# through it looks local unless the proxy headers are checked too.
PROXY_HEADERS = ("cf-connecting-ip", "x-forwarded-for", "forwarded", "x-real-ip")
log = logging.getLogger("zenai.limits")
_lock = threading.Lock()
_hits: dict = defaultdict(deque)          # (bucket, device) -> timestamps
_global = {"day": "", "n": 0}

PAUSE = ("ZenAI is taking a short pause because a lot of messages came in at once. "
         "Try again in a few minutes. If you need someone right now, call or text 988.")


def _hosted() -> bool:
    return bool(os.environ.get("VERCEL"))


def is_local(req: Request) -> bool:
    """True only for a request made on this machine, not one relayed by a tunnel.
    Never true on Vercel: there is no "this machine" there."""
    if _hosted():
        return False
    host = req.client.host if req.client else ""
    return host in LOCAL and not any(req.headers.get(h) for h in PROXY_HEADERS)


def client_ip(req: Request) -> str:
    if _hosted():                          # Vercel sets this itself; clients can't
        fwd = req.headers.get("x-vercel-forwarded-for") or req.headers.get("x-real-ip") or ""
        if fwd.strip():
            return fwd.split(",")[0].strip()
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


def _rules(bucket: str) -> list[tuple[int, int]]:
    from zenai.config import settings

    return ([(600, settings.LIMIT_PER_10MIN), (86400, settings.LIMIT_PER_DAY)] if bucket == "chat"
            else [(600, settings.LIMIT_TTS_PER_10MIN)])


def _redis() -> tuple[str, str] | None:
    url = os.environ.get("KV_REST_API_URL") or os.environ.get("UPSTASH_REDIS_REST_URL")
    tok = os.environ.get("KV_REST_API_TOKEN") or os.environ.get("UPSTASH_REDIS_REST_TOKEN")
    return (url.rstrip("/"), tok) if url and tok else None


def _allow_redis(conn: tuple[str, str], bucket: str, dev: str, now: float) -> bool:
    """Fixed windows in Redis, counted the same way as the memory path: read the
    counts first, and only count the request (device windows AND the shared daily
    total) once it is allowed. A device that is already capped and keeps retrying
    must not use up the campus-wide daily budget for everyone else."""
    import httpx

    from zenai.config import settings

    h = hashlib.sha256(dev.encode()).hexdigest()[:24]
    keys = [(f"zl:{bucket}:{h}:{w}:{int(now // w)}", w, cap) for w, cap in _rules(bucket)]
    if bucket == "chat":
        keys.append((f"zl:global:{time.strftime('%Y-%m-%d', time.gmtime(now))}", 86400, settings.LIMIT_GLOBAL_DAY))
    url, tok = conn
    auth = {"Authorization": f"Bearer {tok}"}

    r = httpx.post(f"{url}/pipeline", json=[["GET", k] for k, _, _ in keys], headers=auth, timeout=1.5)
    r.raise_for_status()
    now_counts = [int(x["result"] or 0) for x in r.json()]
    if any(n >= cap for n, (_, _, cap) in zip(now_counts, keys)):
        return False                       # refused: nothing is counted

    cmds = []
    for k, w, _ in keys:
        cmds += [["INCR", k], ["EXPIRE", k, str(w + 60)]]
    r = httpx.post(f"{url}/pipeline", json=cmds, headers=auth, timeout=1.5)
    r.raise_for_status()
    return True


def allow(req: Request, bucket: str = "chat") -> bool:
    """True if this device may make one more `bucket` request now (and count it)."""
    from zenai.config import settings

    now, dev = time.time(), device(req)
    conn = _redis()
    if conn:
        import httpx

        try:
            return _allow_redis(conn, bucket, dev, now)
        except (httpx.HTTPError, ValueError, KeyError, TypeError, IndexError) as e:
            # Redis down, slow or odd: count in memory instead. Never log the URL or token.
            log.warning("usage limits: Redis unavailable (%s), counting in memory", type(e).__name__)
    rules = _rules(bucket)
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
