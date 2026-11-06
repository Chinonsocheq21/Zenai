"""Shared fixtures. `pg` is a real, throwaway Postgres (pgserver) for the
accounts tests: never the live Neon database."""

import os
import tempfile

import pytest


@pytest.fixture(scope="session")
def pg_url():
    pgserver = pytest.importorskip("pgserver")
    pytest.importorskip("psycopg")
    srv = pgserver.get_server(tempfile.mkdtemp(prefix="zenai-pg-"), cleanup_mode="stop")
    yield srv.get_uri()
    srv.cleanup()


@pytest.fixture
def pg(pg_url, monkeypatch):
    """A migrated, empty database for one test, with the app pointed at it."""
    import psycopg

    from zenai.db import store

    with psycopg.connect(pg_url, autocommit=True) as c:
        c.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
    monkeypatch.setenv("ZENAI_DATABASE_URL", pg_url)
    monkeypatch.setenv("AUTH_SECRET", "test-secret-" + "x" * 40)
    store.migrate()
    with store.connect() as conn:
        yield conn


@pytest.fixture(autouse=True)
def _no_live_database(monkeypatch):
    """Unless a test asks for `pg`, point the app at nothing, so no test can
    ever reach a real database from someone's .env."""
    if "ZENAI_DATABASE_URL" not in os.environ:
        monkeypatch.setenv("ZENAI_DATABASE_URL", "postgresql://nobody@127.0.0.1:1/none")
