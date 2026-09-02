"""Shared pytest fixtures.

DB-dependent tests are skipped automatically when no reachable database is configured,
so the suite runs green in any environment while still exercising every DB-independent
piece of the platform (which is most of the statistical logic).
"""
from __future__ import annotations

import asyncio
import os
import sys

import pytest

if sys.platform == "win32":
    # asyncpg explicitly does not support Windows' default ProactorEventLoop - using it
    # produces intermittent "Event loop is closed" / "assert f is self._write_fut"
    # errors during connection teardown between tests (observed directly in this repo:
    # every failing integration test passed cleanly in isolation, and only failed as
    # part of a larger run, which is the signature of this exact, documented issue).
    # The SelectorEventLoop policy is asyncpg's own recommended workaround.
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

HAS_DB = bool(os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL_TESTS"))

requires_db = pytest.mark.skipif(not HAS_DB, reason="no test database configured (set TEST_DATABASE_URL)")
