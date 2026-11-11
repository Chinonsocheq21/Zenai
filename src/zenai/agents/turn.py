"""One full turn: message in, checked reply out.

    privacy -> crisis -> mood -> route -> memory -> draft -> fidelity -> send

The order is the safety design. The crisis rail runs before the language model
ever sees the message; the Fidelity Monitor runs on every draft before the
student sees it. A rejected draft is rewritten with the monitor's reason, up to
settings.MAX_REWRITES times, then the turn falls back to a protocol-safe reply.

`monitor=False` skips the check and sends the first draft. It exists for one
reason: Experiment E1 needs the drift rate WITHOUT the monitor to compare
against. It is honoured only on the researcher's own machine (a direct call, or
a request zenai.api.main marked local); anywhere else the monitor stays on.
Every turn is logged (redacted text only) to data/turns.jsonl, on that machine only.

History and memory come from the client and are never trusted: they are
redacted and capped here (zenai.agents.privacy) before any model sees them.
The whole turn has one deadline (TURN_DEADLINE_S, under Vercel's 60 s): once
the crisis check has run, a turn that runs out of time sends SAFE_FALLBACK.
"""

from __future__ import annotations

import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path

from zenai.config import settings

LOG = Path(__file__).resolve().parents[3] / "data" / "turns.jsonl"

# Vercel kills a function at 60 s; the turn gives up at 45 and sends the safe reply.
TURN_DEADLINE_S = 45.0

# Set by zenai.api.main for every HTTP request: True only when the request was
# made on this machine (zenai.api.limits.is_local). None means no request at
# all: a script on the researcher's machine calling run() directly.
REQUEST_LOCAL: ContextVar[bool | None] = ContextVar("zenai_request_local", default=None)


def research_allowed() -> bool:
    """May this turn skip the monitor or write the research log?"""
    local = REQUEST_LOCAL.get()
    if local is None:
        return not os.environ.get("VERCEL")
    return local


class _Late(Exception):
    """The turn's deadline passed."""


def _within(deadline: float, fn, *args, **kwargs):
    """Run fn, but stop waiting for it at the deadline. A call still running
    then is abandoned in its own thread; its answer is never used."""
    left = deadline - time.perf_counter()
    if left <= 0.5:
        raise _Late
    pool = ThreadPoolExecutor(1)
    job = pool.submit(fn, *args, **kwargs)
    pool.shutdown(wait=False)
    try:
        return job.result(timeout=left)
    except FutureTimeout:
        raise _Late from None


def _ms(t0: float) -> float:
    return round((time.perf_counter() - t0) * 1000, 1)


def _stage(stage, status, ms=None, detail=""):
    return {"stage": stage, "status": status, "ms": ms, "detail": detail}


def run(text: str, history: list[dict] | None = None, monitor: bool = True,
        memory: list[str] | None = None, client: str = "api", checkin: str | None = None) -> dict:
    import uuid

    from zenai import events
    from zenai.agents import conversation, resources, specialists
    from zenai.agents.privacy import clean_history, clean_memory, redact
    from zenai.models import fidelity
    from zenai.models.crisis import assess
    from zenai.models.distress import classify, which

    trace = []
    tid = uuid.uuid4().hex[:10]

    def add(stage, status, ms=None, detail="", **data):
        trace.append(_stage(stage, status, ms, detail))
        events.publish(tid, "stage", stage=stage, status=status, ms=ms, detail=detail, **data)

    def running(stage):
        events.publish(tid, "stage", stage=stage, status="running")

    t0 = time.perf_counter()
    deadline = t0 + TURN_DEADLINE_S
    # Engineering review H1: a remote caller can't switch the monitor off
    monitor_refused = not monitor and not research_allowed()
    if monitor_refused:
        monitor = True
    history = clean_history(history)
    memory = clean_memory(memory)
    t = time.perf_counter()
    redacted = redact(text)
    n = len(re.findall(r"\[(EMAIL|PHONE|SSN|ID|URL|HANDLE)\]", redacted))
    # the raw message is never published: the viewer sees what the system sees
    events.publish(tid, "turn_start", client=client, text=redacted, monitor=monitor,
                   history=len(history or []), memory=len(memory or []))
    add("privacy", "done", _ms(t), f"{n} item(s) redacted" if n else "nothing identifying found", redacted=n)

    t = time.perf_counter()
    earlier = [h["content"] for h in history if h["role"] == "user"]
    running("crisis")
    # Patterns and conversation rules first. If they already escalate, nothing
    # below calls a model. Otherwise the model screen runs, and the router is
    # started beside it so the screen adds no waiting time; the router's answer
    # is thrown away if the screen escalates.
    quick = assess(redacted, earlier, checkin, screen=False)
    route_job = None
    # Independent of this message: today's date against the campus's own
    # exam_windows (campuses.json), read in its own timezone.
    season_window = specialists.exam_season()
    if quick["risk"] < settings.CRISIS_THRESHOLD:
        tm = time.perf_counter()
        dist = classify(redacted)
        mood = max(dist, key=dist.get)
        mood_ms = _ms(tm)

        pool = ThreadPoolExecutor(1)
        t_route = time.perf_counter()
        route_job = pool.submit(specialists.route, redacted, mood, True, season_window)
        pool.shutdown(wait=False)
        a = assess(redacted, earlier, checkin, screen=True)
    else:
        a = quick
    risk = a["risk"]
    escalate = risk >= settings.CRISIS_THRESHOLD
    add("crisis", "escalated" if escalate else "done", _ms(t),
        f"risk {risk:.2f} vs threshold {settings.CRISIS_THRESHOLD:.2f} · {a['why']}",
        risk=round(risk, 3), threshold=settings.CRISIS_THRESHOLD, context=a["context_signals"], by=a["by"])
    if escalate:
        for s in ("mood", "route", "memory", "conversation", "fidelity", "send"):
            add(s, "skipped", detail="not run — the crisis rail stops the turn here")
        out = {"escalate": True, "crisis_risk": risk, "redacted_text": redacted, "reply": None,
               "attempts": [], "trace": trace, "season": "exams" if season_window else None,
               "escalation": {"hotline": settings.CRISIS_HOTLINE, "campus": settings.CAMPUS_COUNSELING_NAME,
                              "phone": settings.CAMPUS_COUNSELING_PHONE or "NOT CONFIGURED",
                              "action": "human_handoff"},
               "note": "Crisis rail tripped. No reply was generated." + (
                   " The language model never saw this message." if route_job is None else
                   " A model screened the message for risk; nothing was written to the student.")}
        events.publish(tid, "turn_end", escalate=True, reply=None, total_ms=_ms(t0))
        _log(out, monitor)
        return out

    add("mood", "done", mood_ms, f"{mood} {dist[mood]:.0%} · model: {which()}"
        + (f' · checked in today: "{checkin}"' if checkin else ""),
        distress={k: round(v, 3) for k, v in dist.items()})

    running("route")
    try:
        spec = route_job.result(timeout=max(0.0, min(15.0, deadline - time.perf_counter() - 5)))
    except FutureTimeout:   # the router is a nicety; the rules route instantly
        spec = {**specialists.route_rules(redacted, mood, season=season_window), "by": "rules"}
    cards = resources.cards(spec["resources"]) if spec["id"] == "referral" else []
    add("route", "done", _ms(t_route), f"{spec['name']} · {spec['why']}",
        specialist=spec["name"], by=spec.get("by"), resources=[c["name"] for c in cards])

    if memory:
        add("memory", "done", None, f"{len(memory)} note(s) the student chose to keep, from their own device")
    else:
        add("memory", "skipped", detail="nothing saved: memory is off unless the student turns it on")

    # draft -> check -> rewrite, at most MAX_REWRITES times
    attempts, feedback, reply, fallback, late = [], None, None, False, False
    t_draft = time.perf_counter()
    llm_ms, model = 0, "none"
    for i in range(1 + (settings.MAX_REWRITES if monitor else 0)):
        running("conversation")
        try:
            d = _within(deadline, conversation.draft, redacted, history, mood.replace("_", " "), feedback,
                        memory, spec["focus"], checkin, timeout=deadline - time.perf_counter())
        except _Late:
            late = True
            break
        llm_ms += d["ms"]
        model = d["model"]
        events.publish(tid, "draft", n=i + 1, text=d["text"], ms=d["ms"], model=d["model"],
                       rewrite=feedback is not None)
        if not monitor:
            attempts.append({"draft": d["text"], "checked": False})
            reply = d["text"]
            break
        running("fidelity")
        tc = time.perf_counter()
        try:
            chk = _within(deadline, fidelity.verify, d["text"], second_opinion=settings.SECOND_OPINION)
        except _Late:       # an unchecked draft is never sent
            late = True
            break
        events.publish(tid, "check", n=i + 1, drift=chk["drift"], ms=_ms(tc),
                       moves={k: {"flagged": bool(v.get("flagged")), "score": v.get("score"),
                                  "detector_flagged": bool(v.get("detector_flagged")),
                                  "overturned": bool(v.get("overturned")), "sentence": v.get("sentence")}
                              for k, v in chk["moves"].items()},
                       judge=chk.get("judge"))
        flagged = {k: v for k, v in chk["moves"].items() if v.get("flagged")}
        overturned = [k for k, v in chk["moves"].items() if v.get("overturned")]
        attempts.append({"draft": d["text"], "checked": True, "drift": chk["drift"], "overturned": overturned,
                         "flagged": {k: {"score": v["score"], "sentence": v["sentence"]} for k, v in flagged.items()}})
        if not chk["drift"]:
            reply = d["text"]
            break
        feedback = conversation.rewrite_instruction(d["text"], chk["moves"])
    if reply is None:
        reply, fallback = conversation.SAFE_FALLBACK, True

    add("conversation", "done", llm_ms, f"{len(attempts)} draft(s) by {model}"
        + (f" · stopped at the {TURN_DEADLINE_S:.0f} s turn deadline" if late else ""))
    if monitor:
        rejected = sum(1 for a in attempts if a.get("drift"))
        detail = ("first draft passed" if rejected == 0 else
                  f"{rejected} draft(s) rejected and rewritten" + (" · safe fallback used" if fallback else ""))
        if monitor_refused:
            detail += " · monitor can't be turned off from outside the research machine"
        add("fidelity", "done", None, detail, fallback=fallback)
    else:
        add("fidelity", "skipped", detail="monitor OFF — experiment E1 baseline")
    add("send", "done", None, "reply sent")

    out = {"escalate": False, "crisis_risk": risk, "redacted_text": redacted, "distress": dist,
           "primary_emotion": mood, "specialist": {k: spec[k] for k in ("id", "name", "why")},
           "resources": cards, "reply": reply, "attempts": attempts, "fallback": fallback,
           "monitor": monitor, "deadline": late, "trace": trace, "total_ms": _ms(t_draft),
           # a gentle card the app may show, never advice of its own; null outside exam_windows
           "season": "exams" if season_window else None}
    events.publish(tid, "turn_end", escalate=False, reply=reply, fallback=fallback, total_ms=_ms(t0),
                   resources=[c["name"] for c in cards])
    _log(out, monitor)
    return out


def _log(out: dict, monitor: bool) -> None:
    """Redacted text only -- the raw message is never written anywhere. A
    research log on the developer's laptop only: never on the hosted service,
    where nothing a student types is kept, and never for a request that came
    from another machine (a self-hosted server, Engineering review M11)."""
    if os.environ.get("VERCEL") or not research_allowed():
        return
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a") as f:
            f.write(json.dumps({
                "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "monitor": monitor, "text": out["redacted_text"], "escalate": out["escalate"],
                "specialist": (out.get("specialist") or {}).get("id"),
                "reply": out.get("reply"), "attempts": out.get("attempts", []),
                "fallback": out.get("fallback", False),
            }) + "\n")
    except OSError:
        pass
