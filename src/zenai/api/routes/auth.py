"""Sign in with a Morgan email link. No passwords, no email addresses stored.

POST   /auth/start    {email}  -> sends a one-time link (15 minutes)
GET    /auth/verify?token=     -> a "Sign in to ZenAI" page with one button; does NOT use the token
POST   /auth/verify   token=   -> uses the token, sets the session cookie, back to the app
GET    /auth/me                -> who is signed in (or not)
POST   /auth/signout
DELETE /auth/account           -> deletes the account and everything synced to it

Accounts are optional: nothing in chat or the crisis hand-off ever needs one, and
if the database is down these routes say so and the rest of ZenAI carries on.

University mail (Microsoft Safe Links, Proofpoint, Mimecast) opens every link in an
email before the student does, so the emailed link only shows a page; the token is
used when the student presses the button. The link is built from PUBLIC_URL, never
from the Host header, so a forged Host can't send a student's token elsewhere.
"""

from __future__ import annotations

import html
import os
import re
from functools import lru_cache
from urllib.parse import parse_qs, urlsplit

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from zenai import campuses
from zenai.api import limits
from zenai.db import store

router = APIRouter(prefix="/auth", tags=["auth"])

COOKIE = "zenai_session"
EMAIL = re.compile(r"^[^@\s]{1,64}@([a-z0-9-]+\.)+[a-z]{2,}$")
PER_ADDRESS = 3                        # links per address per 15 minutes
SENT = "If that address can use ZenAI, a sign-in link is on its way. It works once, for 15 minutes."
OUTBOX: list[dict] = []                # local and tests: links land here instead of an inbox
HOSTED_URL = "https://zenai-app.vercel.app"   # used when PUBLIC_URL is unset and the request isn't local


_DEFAULT_DOMAINS = ",".join(d for c in campuses.all_campuses() for d in c["domains"])


def domains() -> list[str]:
    return [d.strip().lower() for d in os.environ.get("AUTH_DOMAINS", _DEFAULT_DOMAINS).split(",") if d.strip()]


def allowed(email: str) -> bool:
    dom = email.rsplit("@", 1)[-1]
    return any(dom == d or dom.endswith("." + d) for d in domains())


@lru_cache(maxsize=1)
def _migrated() -> bool:
    store.migrate()
    return True


def _db():
    """A connection with the schema in place, or a calm 503."""
    try:
        _migrated()
        return store.connect()
    except store.Unavailable as e:
        _migrated.cache_clear()
        raise HTTPException(503, {"unavailable": True, "message": "Accounts aren't available right now. "
                                  "You can keep using ZenAI without signing in."}) from e


def _send(to: str, link: str) -> None:
    text = (f"Here is your link to sign in to ZenAI:\n\n{link}\n\nIt works once and expires in 15 minutes. "
            "If you didn't ask for this, you can ignore this email.\n\n"
            "ZenAI is not a counselor. If you are in crisis, call or text 988.")
    html = (f'<p>Here is your link to sign in to ZenAI:</p><p><a href="{link}" style="display:inline-block;'
            'padding:12px 20px;border-radius:999px;background:#1B3D6F;color:#fff;text-decoration:none;'
            'font-weight:600">Sign in to ZenAI</a></p><p>It works once and expires in 15 minutes. If you '
            "didn't ask for this, you can ignore this email.</p><p style=\"color:#7C8599;font-size:13px\">"
            "ZenAI is not a counselor. If you are in crisis, call or text 988.</p>")
    key = os.environ.get("RESEND_API_KEY")
    if not key:
        if os.environ.get("VERCEL"):
            raise HTTPException(503, {"unavailable": True, "message": "Sign-in emails aren't set up yet."})
        OUTBOX.append({"to": to, "link": link, "text": text})
        return
    import httpx

    r = httpx.post("https://api.resend.com/emails", timeout=10, headers={"Authorization": f"Bearer {key}"},
                   json={"from": os.environ.get("MAIL_FROM", "ZenAI <onboarding@resend.dev>"), "to": [to],
                         "subject": "Your ZenAI sign-in link", "text": text, "html": html})
    if r.status_code >= 400:
        raise HTTPException(502, {"message": "The sign-in email couldn't be sent. Try again in a minute."})


def _secure(req: Request) -> bool:
    return req.url.scheme == "https" or req.headers.get("x-forwarded-proto") == "https" or bool(os.environ.get("VERCEL"))


def _sid(req: Request) -> str | None:
    return req.cookies.get(COOKIE)


def public_base(req: Request) -> str:
    """Where emailed links point. PUBLIC_URL wins; the request's own URL is trusted only
    for a request made on this machine; anything else gets the production address."""
    configured = os.environ.get("PUBLIC_URL", "").strip().rstrip("/")
    if configured:
        return configured
    if limits.is_local(req):
        return str(req.base_url).rstrip("/")
    return HOSTED_URL


def verify_link(req: Request, raw: str) -> str:
    path = urlsplit(str(req.url_for("verify"))).path     # keeps a mount prefix (/api on Vercel), drops the Host
    return f"{public_base(req)}{path}?token={raw}"


def _same_site(req: Request) -> bool:
    """A browser POST carries Origin. Refuse one from another site (login CSRF)."""
    origin = req.headers.get("origin")
    if not origin or origin == "null":
        return True
    host = urlsplit(origin).netloc.lower()
    ok = {req.headers.get("host", "").lower(), urlsplit(public_base(req)).netloc.lower()}
    return host in ok


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex">
<title>Sign in to ZenAI</title>
<style>
:root{--bg:#F5F1EA;--card:#fff;--ink:#14233D;--muted:#5F6878;--blue:#1B3D6F;--line:rgba(20,35,61,.09);
--sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
--serif:"New York","Iowan Old Style","Apple Garamond",Georgia,"Times New Roman",serif}
@media (prefers-color-scheme:dark){:root{--bg:#0F1726;--card:#18233A;--ink:#EEF1F6;--muted:#A3ADBF;--blue:#7FA6E0;--line:rgba(255,255,255,.1)}}
*{box-sizing:border-box}
body{margin:0;min-height:100vh;display:grid;place-items:center;background:var(--bg);color:var(--ink);font-family:var(--sans);-webkit-font-smoothing:antialiased;padding:24px}
main{background:var(--card);border:1px solid var(--line);border-radius:22px;padding:36px 28px;max-width:380px;width:100%;text-align:center;box-shadow:0 8px 24px -10px rgba(20,35,61,.16)}
.orb{width:56px;height:56px;border-radius:50%;margin:0 auto 18px;background:radial-gradient(circle at 35% 30%,#FFD9B0,#F08A4B 45%,#1B3D6F)}
h1{font-family:var(--serif);font-weight:400;font-size:28px;margin:0 0 10px}
p{color:var(--muted);line-height:1.5;margin:0 0 22px}
button{font:inherit;font-weight:600;font-size:16px;border:0;border-radius:999px;padding:14px 26px;width:100%;background:var(--blue);color:#fff;cursor:pointer}
@media (prefers-color-scheme:dark){button{color:#0F1726}}
button:focus-visible{outline:3px solid #E8792F;outline-offset:3px}
small{display:block;margin-top:22px;color:var(--muted);font-size:13px}
</style></head>
<body><main>
<div class="orb" aria-hidden="true"></div>
<h1>Sign in to ZenAI</h1>
<p>Press the button to finish signing in on this device.</p>
<form method="post" action="verify">
<input type="hidden" name="token" value="{token}">
<button type="submit">Sign in to ZenAI</button>
</form>
<small>ZenAI is not a counselor. If you are in crisis, call or text 988.</small>
</main></body></html>
"""


class StartIn(BaseModel):
    email: str = Field(..., max_length=254)


@router.post("/start")
def start(body: StartIn, req: Request) -> dict:
    email = body.email.strip().lower()
    if not EMAIL.match(email):
        raise HTTPException(422, {"message": "That doesn't look like an email address."})
    if not allowed(email):
        raise HTTPException(422, {"message": f"Use your {(campuses.by_domain(domains()[0]) or campuses.default())['name']} email (@{domains()[0]})."})
    if not limits.allow(req, "tts"):           # per device: the light bucket
        raise HTTPException(429, {"message": "Too many tries. Wait a few minutes and try again."})
    with _db() as conn:
        if store.recent_login_tokens(conn, email) >= PER_ADDRESS:
            return {"sent": True, "message": SENT}   # same answer: don't flood an inbox, don't reveal anything
        raw = store.create_login_token(conn, email)
    _send(email, verify_link(req, raw))
    return {"sent": True, "message": SENT}


@router.get("/verify", name="verify")
def verify_page(token: str = "") -> Response:
    """What a mail scanner (or the student) sees on opening the link. It never looks the
    token up, so it can't use it and can't say whether it's valid."""
    return HTMLResponse(PAGE.replace("{token}", html.escape(token[:200], quote=True)),
                        headers={"Cache-Control": "no-store", "X-Robots-Tag": "noindex"})


@router.post("/verify", name="verify_post")
async def verify(req: Request) -> Response:
    """The button on that page: uses the token once and signs this browser in."""
    form = parse_qs((await req.body()).decode("utf-8", "replace"))
    token = (form.get("token") or [""])[0]
    return await run_in_threadpool(_sign_in, req, token)


def _sign_in(req: Request, token: str) -> Response:
    home = "/app/"
    if not token or not _same_site(req):
        return RedirectResponse(f"{home}?signin=expired", status_code=303)
    try:
        with _db() as conn:
            uid = store.consume_login_token(conn, token)
            if not uid:
                return RedirectResponse(f"{home}?signin=expired", status_code=303)
            sid = store.create_session(conn, uid)
    except HTTPException:
        return RedirectResponse(f"{home}?signin=unavailable", status_code=303)
    r = RedirectResponse(f"{home}?signin=ok", status_code=303)
    r.set_cookie(COOKIE, sid, max_age=int(store.SESSION_TTL.total_seconds()), httponly=True,
                 secure=_secure(req), samesite="lax", path="/")
    return r


@router.get("/me")
def me(req: Request) -> dict:
    if not _sid(req):
        return {"signed_in": False}
    try:
        with _db() as conn:
            u = store.user_for_session(conn, _sid(req))
    except HTTPException:
        return {"signed_in": False, "available": False}
    if not u:
        return {"signed_in": False}
    return {"signed_in": True, "campus": u["campus"], "sync_checkins": u["sync_checkins"]}


@router.post("/signout")
def signout(req: Request, response: Response) -> dict:
    if _sid(req):
        try:
            with _db() as conn:
                store.end_session(conn, _sid(req))
        except HTTPException:
            pass
    response.delete_cookie(COOKIE, path="/")
    return {"signed_in": False}


@router.delete("/account")
def delete_account(req: Request, response: Response) -> dict:
    with _db() as conn:
        u = store.user_for_session(conn, _sid(req))
        if not u:
            raise HTTPException(401, {"message": "You're not signed in."})
        store.delete_user(conn, u["id"])
    response.delete_cookie(COOKIE, path="/")
    return {"deleted": True}
