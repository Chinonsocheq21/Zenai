"""Campus resources the Resource & Referral specialist can show.

Curated, never generated: the language model does not write phone numbers or
names of offices, because a wrong number in this setting is worse than none.
The entries live in the campus registry (zenai/campuses.json), one set per
campus; Morgan's were read off morgan.edu on the date in VERIFIED. Re-check them each
semester; offices move.

These are shown as cards beside the reply, only when the student ASKS for help
of that kind. The reply itself stays on protocol (no advice): offering a
resource the student asked for is answering a question, not telling them what
to do.
"""

from __future__ import annotations

from zenai import campuses

_DEFAULT = campuses.default()
VERIFIED = _DEFAULT["resources_verified"]
RESOURCES = _DEFAULT["resources"]


def _normalize(topic: str) -> str:
    """A loose key for topic matching: lowercase, spaces/dashes to underscores.

    Lets a caller pass a phrase like 'financial aid' or 'Housing' and still
    land on the resource keyed 'financial_aid' or 'housing'.
    """
    return str(topic).strip().lower().replace(" ", "_").replace("-", "_")


def cards(topics: list[str], campus_id: str | None = None) -> list[dict]:
    """The cards for these topics, in order, with S.O.S. as the catch-all."""
    campus = (campuses.get(campus_id) if campus_id else None) or _DEFAULT
    res, verified = campus["resources"], campus["resources_verified"]
    by_norm = {_normalize(k): k for k in res}
    keys = [by_norm[_normalize(t)] for t in topics if _normalize(t) in by_norm] or ["support"]
    return [{"id": k, **res[k], "verified": res[k].get("verified", verified)} for k in dict.fromkeys(keys)]
