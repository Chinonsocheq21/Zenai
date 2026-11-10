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


# What the client may send along with a message. The server never trusts it:
# every item is redacted and capped here, on every request, before any model
# sees it (Engineering review H2, H3, M4).
HISTORY_TURNS = 16
HISTORY_CHARS = 1000
MEMORY_NOTES = 10
MEMORY_CHARS = 200


def clean_history(history: list[dict] | None) -> list[dict]:
    """The last 16 user/assistant turns, 1,000 characters each, redacted.
    Any other role (a forged "system" turn) is dropped."""
    out = []
    for h in history or []:
        if not isinstance(h, dict) or h.get("role") not in ("user", "assistant"):
            continue
        content = h.get("content")
        if not isinstance(content, str) or not content.strip():
            continue
        # redact a little past the cut first, so the cut can never leave half a
        # phone number or address behind
        out.append({"role": h["role"], "content": redact(content[:HISTORY_CHARS + 100])[:HISTORY_CHARS]})
    return out[-HISTORY_TURNS:]


def clean_memory(memory: list[str] | None) -> list[str]:
    """At most 10 notes of 200 characters each, redacted."""
    notes = [m for m in (memory or []) if isinstance(m, str) and m.strip()]
    return [redact(m[:MEMORY_CHARS + 100])[:MEMORY_CHARS] for m in notes[:MEMORY_NOTES]]
