"""Accounts storage, kept as small as the product allows.

What is stored, and what is deliberately NOT:
  * No email addresses. A student is found by HMAC(email, AUTH_SECRET), so a
    leaked table can't be turned back into a list of who uses ZenAI.
  * Sign-in links and sessions are stored only as SHA-256 hashes, so a leaked
    table can't be used to sign in.
  * Check-ins only for students who turned syncing on, as a day and a level.
    Never a message, never a reply.
  * Pilot requests (from the For universities page) are business contacts that
    the sender typed in on purpose, so those are kept as written.

Postgres (Neon on Vercel). One short-lived connection per call: serverless
functions don't keep pools, and Neon's pooled URL does the pooling.
Migrations are plain SQL, applied in order and recorded in schema_migrations.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from datetime import date, datetime, timedelta, timezone

MIGRATIONS: list[tuple[int, str]] = [
    (1, """
    CREATE TABLE users (
        id           BIGSERIAL PRIMARY KEY,
        email_hmac   TEXT UNIQUE NOT NULL,
        campus       TEXT NOT NULL DEFAULT 'morgan.edu',
        sync_checkins BOOLEAN NOT NULL DEFAULT FALSE,
        created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
        last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE TABLE login_tokens (
        token_hash  TEXT PRIMARY KEY,
        email_hmac  TEXT NOT NULL,
        expires_at  TIMESTAMPTZ NOT NULL,
        used_at     TIMESTAMPTZ
    );
    CREATE INDEX login_tokens_email ON login_tokens (email_hmac, expires_at);
    CREATE TABLE sessions (
        session_hash TEXT PRIMARY KEY,
        user_id      BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
        expires_at   TIMESTAMPTZ NOT NULL
    );
    CREATE TABLE checkins (
        user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        day     DATE NOT NULL,
        level   SMALLINT NOT NULL CHECK (level BETWEEN 0 AND 4),
        PRIMARY KEY (user_id, day)
    );
    CREATE TABLE pilot_requests (
        id          BIGSERIAL PRIMARY KEY,
        name        TEXT NOT NULL,
        email       TEXT NOT NULL,
        institution TEXT NOT NULL,
        role        TEXT NOT NULL DEFAULT '',
        message     TEXT NOT NULL DEFAULT '',
        created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """),
    (2, """
    CREATE TABLE usage_weekly (
        week   DATE NOT NULL,
        campus TEXT NOT NULL,
        metric TEXT NOT NULL,
        n      INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY (week, campus, metric)
    );
    """),
    (3, """
    ALTER TABLE users ALTER COLUMN email_hmac DROP NOT NULL;
    """),
]

LOGIN_TTL = timedelta(minutes=15)
SESSION_TTL = timedelta(days=30)


class Unavailable(RuntimeError):
    """No database configured or reachable. Callers degrade; chat never depends on this."""


def url() -> str:
    from zenai.config import settings

    u = os.environ.get("ZENAI_DATABASE_URL") or os.environ.get("DATABASE_URL") or settings.DATABASE_URL
    return u.replace("postgresql+psycopg://", "postgresql://")


def connect():
    try:
        import psycopg
    except ImportError as e:
        raise Unavailable("psycopg not installed") from e
    try:
        return psycopg.connect(url(), autocommit=True, connect_timeout=4)
    except psycopg.OperationalError as e:
        raise Unavailable(type(e).__name__) from e


def ping() -> bool:
    try:
        with connect() as c:
            c.execute("SELECT 1")
        return True
    except Unavailable:
        return False


def migrate(conn=None) -> list[int]:
    """Apply any migrations not yet recorded. Safe to run on every cold start."""
    own = conn is None
    conn = conn or connect()
    try:
        conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version INT PRIMARY KEY, at TIMESTAMPTZ DEFAULT now())")
        done = {r[0] for r in conn.execute("SELECT version FROM schema_migrations")}
        applied = []
        for v, sql in MIGRATIONS:
            if v in done:
                continue
            with conn.transaction():
                conn.execute(sql)
                conn.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (v,))
            applied.append(v)
        return applied
    finally:
        if own:
            conn.close()


# ---------------------------------------------------------------- identities
def _secret() -> bytes:
    s = os.environ.get("AUTH_SECRET", "")
    if len(s) < 32:
        raise Unavailable("AUTH_SECRET is not set (32+ characters)")
    return s.encode()


def email_hmac(email: str) -> str:
    return hmac.new(_secret(), email.strip().lower().encode(), hashlib.sha256).hexdigest()


def _h(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_login_token(conn, email: str, ttl: timedelta = LOGIN_TTL) -> str:
    """A one-time sign-in token for this address. Only its hash is stored."""
    raw = secrets.token_urlsafe(32)
    conn.execute("INSERT INTO login_tokens (token_hash, email_hmac, expires_at) VALUES (%s, %s, %s)",
                 (_h(raw), email_hmac(email), _now() + ttl))
    return raw


def recent_login_tokens(conn, email: str, within: timedelta = LOGIN_TTL) -> int:
    """How many links were sent to this address lately (to stop someone flooding an inbox)."""
    row = conn.execute("SELECT count(*) FROM login_tokens WHERE email_hmac = %s AND expires_at > %s",
                       (email_hmac(email), _now() - within + LOGIN_TTL)).fetchone()
    return int(row[0])


def consume_login_token(conn, raw: str) -> int | None:
    """Single use: returns the user id (creating the user on first sign-in), or None."""
    row = conn.execute(
        "UPDATE login_tokens SET used_at = now() WHERE token_hash = %s AND used_at IS NULL AND expires_at > now() "
        "RETURNING email_hmac", (_h(raw),)).fetchone()
    if not row:
        return None
    uid = conn.execute(
        "INSERT INTO users (email_hmac) VALUES (%s) ON CONFLICT (email_hmac) DO UPDATE SET last_seen_at = now() "
        "RETURNING id", (row[0],)).fetchone()[0]
    return int(uid)


def create_invite_user(conn, campus: str) -> int:
    """An anonymous member made by redeeming an invite code: no email at all, just
    a campus and a random id (email_hmac stays NULL; migration 3 dropped its
    NOT NULL so this and the email sign-in can share the same table)."""
    row = conn.execute("INSERT INTO users (campus) VALUES (%s) RETURNING id", (campus,)).fetchone()
    return int(row[0])


def create_session(conn, user_id: int, ttl: timedelta = SESSION_TTL) -> str:
    raw = secrets.token_urlsafe(32)
    conn.execute("INSERT INTO sessions (session_hash, user_id, expires_at) VALUES (%s, %s, %s)",
                 (_h(raw), user_id, _now() + ttl))
    return raw


def user_for_session(conn, raw: str | None) -> dict | None:
    if not raw:
        return None
    row = conn.execute(
        "SELECT u.id, u.campus, u.sync_checkins FROM sessions s JOIN users u ON u.id = s.user_id "
        "WHERE s.session_hash = %s AND s.expires_at > now()", (_h(raw),)).fetchone()
    return {"id": int(row[0]), "campus": row[1], "sync_checkins": bool(row[2])} if row else None


def end_session(conn, raw: str) -> None:
    conn.execute("DELETE FROM sessions WHERE session_hash = %s", (_h(raw),))


def delete_user(conn, user_id: int) -> None:
    """Everything about this student, gone: sessions and check-ins cascade."""
    conn.execute("DELETE FROM users WHERE id = %s", (user_id,))


# ---------------------------------------------------------------- check-ins
def set_sync(conn, user_id: int, on: bool) -> None:
    conn.execute("UPDATE users SET sync_checkins = %s WHERE id = %s", (on, user_id))
    if not on:                               # turning it off removes what was synced
        conn.execute("DELETE FROM checkins WHERE user_id = %s", (user_id,))


def put_checkin(conn, user_id: int, day: date, level: int) -> bool:
    """Stored only if the student turned syncing on. Returns whether it was stored."""
    row = conn.execute(
        "INSERT INTO checkins (user_id, day, level) SELECT %s, %s, %s WHERE EXISTS "
        "(SELECT 1 FROM users WHERE id = %s AND sync_checkins) "
        "ON CONFLICT (user_id, day) DO UPDATE SET level = EXCLUDED.level RETURNING 1",
        (user_id, day, level, user_id)).fetchone()
    return bool(row)


def checkins(conn, user_id: int, since: date) -> list[dict]:
    rows = conn.execute("SELECT day, level FROM checkins WHERE user_id = %s AND day >= %s ORDER BY day",
                        (user_id, since)).fetchall()
    return [{"day": d.isoformat(), "level": int(lv)} for d, lv in rows]


# ---------------------------------------------------------------- pilots
def add_pilot_request(conn, name: str, email: str, institution: str, role: str = "", message: str = "") -> int:
    return int(conn.execute(
        "INSERT INTO pilot_requests (name, email, institution, role, message) VALUES (%s, %s, %s, %s, %s) RETURNING id",
        (name, email, institution, role, message)).fetchone()[0])


# ---------------------------------------------------------------- campus trends
def bump(conn, week: date, campus: str, metrics: dict[str, int]) -> None:
    """Add to this week's counters. Counts only: no text, no ids, no timestamps finer than a week."""
    for metric, n in metrics.items():
        conn.execute(
            "INSERT INTO usage_weekly (week, campus, metric, n) VALUES (%s, %s, %s, %s) "
            "ON CONFLICT (week, campus, metric) DO UPDATE SET n = usage_weekly.n + EXCLUDED.n",
            (week, campus, metric, n))


def weekly(conn, campus: str, since: date) -> list[tuple[date, str, int]]:
    return [(w, m, int(n)) for w, m, n in conn.execute(
        "SELECT week, metric, n FROM usage_weekly WHERE campus = %s AND week >= %s ORDER BY week, metric",
        (campus, since)).fetchall()]
