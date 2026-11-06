"""Accounts storage: what is kept, what never is, and that it all goes on delete."""

from datetime import datetime, timedelta, timezone

from zenai.db import store


def test_migrations_apply_once(pg):
    assert store.migrate(pg) == []                       # already applied by the fixture
    tables = {r[0] for r in pg.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")}
    assert {"users", "login_tokens", "sessions", "checkins", "pilot_requests", "schema_migrations"} <= tables


def test_no_email_or_raw_token_is_stored(pg):
    raw = store.create_login_token(pg, "Student@Morgan.edu")
    dump = " ".join(str(r) for t in ("users", "login_tokens", "sessions")
                    for r in pg.execute(f"SELECT * FROM {t}").fetchall())
    assert "morgan.edu" not in dump.lower() and "student" not in dump.lower()
    assert raw not in dump
    uid = store.consume_login_token(pg, raw)
    sid = store.create_session(pg, uid)
    dump = " ".join(str(r) for r in pg.execute("SELECT * FROM sessions").fetchall())
    assert sid not in dump


def test_login_token_is_single_use_and_expires(pg):
    raw = store.create_login_token(pg, "a@morgan.edu")
    uid = store.consume_login_token(pg, raw)
    assert uid and store.consume_login_token(pg, raw) is None
    old = store.create_login_token(pg, "a@morgan.edu", ttl=timedelta(seconds=-1))
    assert store.consume_login_token(pg, old) is None
    assert store.consume_login_token(pg, "made-up") is None


def test_same_address_same_student_any_case(pg):
    a = store.consume_login_token(pg, store.create_login_token(pg, "Kim@Morgan.edu"))
    b = store.consume_login_token(pg, store.create_login_token(pg, " kim@morgan.edu "))
    c = store.consume_login_token(pg, store.create_login_token(pg, "lee@morgan.edu"))
    assert a == b != c


def test_sessions(pg):
    uid = store.consume_login_token(pg, store.create_login_token(pg, "s@morgan.edu"))
    sid = store.create_session(pg, uid)
    assert store.user_for_session(pg, sid)["id"] == uid
    assert store.user_for_session(pg, "nope") is None and store.user_for_session(pg, None) is None
    store.end_session(pg, sid)
    assert store.user_for_session(pg, sid) is None
    expired = store.create_session(pg, uid, ttl=timedelta(seconds=-1))
    assert store.user_for_session(pg, expired) is None


def test_checkins_only_when_sync_is_on_and_removed_when_off(pg):
    uid = store.consume_login_token(pg, store.create_login_token(pg, "c@morgan.edu"))
    today = datetime.now(timezone.utc).date()
    assert store.put_checkin(pg, uid, today, 2) is False          # off by default
    assert store.checkins(pg, uid, today - timedelta(days=30)) == []
    store.set_sync(pg, uid, True)
    assert store.put_checkin(pg, uid, today, 2) and store.put_checkin(pg, uid, today, 3)   # same day: updated
    assert store.checkins(pg, uid, today - timedelta(days=30)) == [{"day": today.isoformat(), "level": 3}]
    store.set_sync(pg, uid, False)
    assert store.checkins(pg, uid, today - timedelta(days=30)) == []


def test_delete_removes_everything(pg):
    uid = store.consume_login_token(pg, store.create_login_token(pg, "d@morgan.edu"))
    store.create_session(pg, uid)
    store.set_sync(pg, uid, True)
    store.put_checkin(pg, uid, datetime.now(timezone.utc).date(), 1)
    store.delete_user(pg, uid)
    for t in ("users", "sessions", "checkins"):
        assert pg.execute(f"SELECT count(*) FROM {t}").fetchone()[0] == 0


def test_unreachable_database_is_reported_not_raised(monkeypatch):
    monkeypatch.setenv("ZENAI_DATABASE_URL", "postgresql://nobody@127.0.0.1:1/none")
    assert store.ping() is False
