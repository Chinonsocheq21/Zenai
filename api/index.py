"""Vercel entry point: the whole ZenAI API as one Python function under /api.

Vercel hands the function the full path (/api/chat), so the real app is mounted
under /api here and sees the same paths it sees locally (/chat). Nothing else
changes between the laptop and Vercel.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]

from fastapi import FastAPI

from zenai.api.main import app as zenai

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/api", zenai)
