"""Sign in with a Morgan email link. No passwords, no email addresses stored.

POST   /auth/start    {email}  -> sends a one-time link (15 minutes)
GET    /auth/verify?token=     -> signs in, sets the session cookie, back to the app
GET    /auth/me                -> who is signed in (or not)
POST   /auth/signout
DELETE /auth/account           -> deletes the account and everything synced to it

Accounts are optional: nothing in chat or the crisis hand-off ever needs one, and
if the database is down these routes say so and the rest of ZenAI carries on.
"""

from __future__ import annotations

import os
import re
from functools import lru_cache

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from zenai.api import limits
from zenai.db import store

router = APIRouter(prefix="/auth", tags=["auth"])

COOKIE = "zenai_session"
EMAIL = re.compile(r"^[^@\s]{1,64}@([a-z0-9-]+\.)+[a-z]{2,}$")
PER_ADDRESS = 3                        # links per address per 15 minutes
SENT = "If that address can use ZenAI, a sign-in link is on its way. It works once, for 15 minutes."
OUTBOX: list[dict] = []                # local and tests: links land here instead of an inbox


def domains() -> list[str]:
    return [d.strip().lower() for d in os.environ.get("AUTH_DOMAINS", "morgan.edu").split(",") if d.strip()]


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


class StartIn(BaseModel):
    email: str = Field(..., max_length=254)


@router.post("/start")
def start(body: StartIn, req: Request) -> dict:
    email = body.email.strip().lower()
    if not EMAIL.match(email):
        raise HTTPException(422, {"message": "That doesn't look like an email address."})
    if not allowed(email):
        raise HTTPException(422, {"message": f"Use your Morgan State email (@{domains()[0]})."})
    if not limits.allow(req, "tts"):           # per device: the light bucket
        raise HTTPException(429, {"message": "Too many tries. Wait a few minutes and try again."})
    with _db() as conn:
        if store.recent_login_tokens(conn, email) >= PER_ADDRESS:
            return {"sent": True, "message": SENT}   # same answer: don't flood an inbox, don't reveal anything
        raw = store.create_login_token(conn, email)
    base = str(req.url_for("verify"))
    _send(email, f"{base}?token={raw}")
    return {"sent": True, "message": SENT}


@router.get("/verify", name="verify")
def verify(token: str, req: Request) -> Response:
    home = "/app/"
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
