"""Usage limits: per-device and per-IP windows plus a global daily cap.

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
Every request counts against its device (or signed-in account) AND its IP
address (client_ip; on Vercel, x-vercel-forwarded-for), so rotating the device
header does not buy a fresh allowance. A refused request is counted nowhere.
Device ids and IPs are hashed (keyed) before they become Redis keys.

A crisis is never limited: chat.py runs the crisis check before it asks here.
"""

from __future__ import annotations

import hashlib
import hmac
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
_hits: dict = defaultdict(deque)          # (bucket, device or "addr:"+ip) -> timestamps
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


_accounts: dict[str, tuple[int, float]] = {}      # session hash -> (user id, cached until)


def _account(req: Request) -> str | None:
    """A signed-in student's limits follow the account, not the device, so a phone
    and a laptop share one allowance. Any trouble here falls back to the device."""
    sid = req.cookies.get("zenai_session")
    if not sid:
        return None
    key, now = hashlib.sha256(sid.encode()).hexdigest(), time.time()
    hit = _accounts.get(key)
    if hit and hit[1] > now:
        return f"acct:{hit[0]}"
    try:
        from zenai.db import store

        with store.connect() as conn:
            u = store.user_for_session(conn, sid)
    except Exception:  # noqa: BLE001 -- the database is optional for limits
        return None
    if not u:
        return None
    if len(_accounts) > 5000:
        _accounts.clear()
    _accounts[key] = (u["id"], now + 300)
    return f"acct:{u['id']}"


def device(req: Request) -> str:
    acct = _account(req)
    if acct:
        return acct
    d = (req.headers.get("x-zenai-device") or "").strip()[:64]
    return d or f"ip:{client_ip(req)}"


def check_code(req: Request) -> None:
    from zenai.config import settings

    if settings.ACCESS_CODE and (req.headers.get("x-zenai-code") or "").strip().upper() != settings.ACCESS_CODE.upper():
        raise HTTPException(401, {"code_required": True, "message": "Enter the class code to use ZenAI."})


# Per-IP windows. Rotating the X-ZenAI-Device header gives a fresh device
# allowance, so every request ALSO counts against the address it came from. A
# campus shares a few public addresses (dorm Wi-Fi, eduroam), so these are far
# above one person's use but far below what a script needs to drain the daily total.
IP_PER_10MIN = 60                     # chat messages per IP in any 10 minutes
IP_PER_DAY = 400                      # chat messages per IP per day
PILOT_PER_HOUR = 5                    # pilot requests per device AND per IP per hour
PILOT_WINDOW = 3600


def _rules(bucket: str) -> list[tuple[str, int, int]]:
    """(scope, window seconds, cap) for a bucket; scope is "dev" or "ip"."""
    from zenai.config import settings

    if bucket == "chat":
        return [("dev", 600, settings.LIMIT_PER_10MIN), ("dev", 86400, settings.LIMIT_PER_DAY),
                ("ip", 600, IP_PER_10MIN), ("ip", 86400, IP_PER_DAY)]
    if bucket == "pilot":
        return [("dev", PILOT_WINDOW, PILOT_PER_HOUR), ("ip", PILOT_WINDOW, PILOT_PER_HOUR)]
    return [("dev", 600, settings.LIMIT_TTS_PER_10MIN)]


def _redis() -> tuple[str, str] | None:
    url = os.environ.get("KV_REST_API_URL") or os.environ.get("UPSTASH_REDIS_REST_URL")
    tok = os.environ.get("KV_REST_API_TOKEN") or os.environ.get("UPSTASH_REDIS_REST_TOKEN")
    return (url.rstrip("/"), tok) if url and tok else None


def _hash(value: str) -> str:
    """Keyed hash for Redis keys. An IPv4 address has so few possible values that a
    plain hash could be reversed by trying them all, so mix in the server secret."""
    salt = (os.environ.get("AUTH_SECRET") or "zenai-limits").encode()
    return hmac.new(salt, value.encode(), hashlib.sha256).hexdigest()[:24]


def _allow_redis(conn: tuple[str, str], bucket: str, subjects: dict[str, str], now: float) -> bool:
    """Fixed windows in Redis, counted the same way as the memory path: read the
    counts first, and only count the request (device windows, IP windows AND the
    shared daily total) once it is allowed. A device or address that is already
    capped and keeps retrying must not use up anyone else's budget."""
    import httpx

    from zenai.config import settings

    hashed = {scope: _hash(v) for scope, v in subjects.items()}
    keys = [(f"zl:{bucket}:{'ip:' if scope == 'ip' else ''}{hashed[scope]}:{w}:{int(now // w)}", w, cap)
            for scope, w, cap in _rules(bucket)]
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
    """True if this device AND this address may make one more `bucket` request now
    (and count it against both). Buckets: "chat", "tts", "pilot"."""
    from zenai.config import settings

    now = time.time()
    subjects = {"dev": device(req), "ip": client_ip(req)}
    conn = _redis()
    if conn:
        import httpx

        try:
            return _allow_redis(conn, bucket, subjects, now)
        except (httpx.HTTPError, ValueError, KeyError, TypeError, IndexError) as e:
            # Redis down, slow or odd: count in memory instead. Never log the URL or token.
            log.warning("usage limits: Redis unavailable (%s), counting in memory", type(e).__name__)
    rules = _rules(bucket)
    with _lock:
        scopes = {s for s, _, _ in rules}
        names = {"dev": subjects["dev"], "ip": "addr:" + subjects["ip"]}
        queues = {scope: _hits[(bucket, names[scope])] for scope in scopes}
        for q in queues.values():
            while q and now - q[0] > 86400:
                q.popleft()
        for scope, window, cap in rules:
            if sum(1 for t in queues[scope] if now - t <= window) >= cap:
                return False               # refused: nothing is counted
        if bucket == "chat":
            day = time.strftime("%Y-%m-%d")
            if _global["day"] != day:
                _global.update(day=day, n=0)
            if _global["n"] >= settings.LIMIT_GLOBAL_DAY:
                return False
            _global["n"] += 1
        for q in queues.values():
            q.append(now)
        return True


def reset() -> None:
    _accounts.clear()
    with _lock:
        _hits.clear()
        _global.update(day="", n=0)
