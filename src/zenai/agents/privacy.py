"""Tier 0, step 1. Runs before anything else sees the text.

Deliberately boring and deterministic -- a regex you can read beats a model you
have to trust for the thing that must not fail silently.
"""

from __future__ import annotations

import re

PATTERNS: list[tuple[str, re.Pattern]] = [
    ("[EMAIL]", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b")),
    ("[PHONE]", re.compile(r"\b(?:\+?1[-. ]?)?\(?\d{3}\)?[-. ]?\d{3}[-. ]?\d{4}\b")),
    ("[SSN]", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    # Morgan student IDs. 7 digits added Oct 29: the held-out red-team set's
    # "Student number 7319042" got through when this matched 8 to 10 only.
    ("[ID]", re.compile(r"(?i)\b(?:student\s*(?:id|number|no\.?|#)|id\s*(?:number|no\.?|#)?)\s*[:#]?\s*\d{4,10}\b|\b\d{7,10}\b")),
    ("[URL]", re.compile(r"https?://\S+")),
    ("[HANDLE]", re.compile(r"(?<!\w)@[A-Za-z_]\w{2,}")),
]


def redact(text: str) -> str:
    for token, pat in PATTERNS:
        text = pat.sub(token, text)
    return text
