"""One full turn: message in, checked reply out.

    privacy -> crisis -> mood -> memory -> draft -> fidelity -> send

The order is the safety design. The crisis rail runs before the language model
ever sees the message; the Fidelity Monitor runs on every draft before the
student sees it. A rejected draft is rewritten with the monitor's reason, up to
settings.MAX_REWRITES times, then the turn falls back to a protocol-safe reply.

`monitor=False` skips the check and sends the first draft. It exists for one
reason: Experiment E1 needs the drift rate WITHOUT the monitor to compare
against. Every turn is logged (redacted text only) to data/turns.jsonl.
"""

from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from zenai.config import settings

LOG = Path(__file__).resolve().parents[3] / "data" / "turns.jsonl"


def _ms(t0: float) -> float:
    return round((time.perf_counter() - t0) * 1000, 1)


def _stage(stage, status, ms=None, detail=""):
    return {"stage": stage, "status": status, "ms": ms, "detail": detail}


def run(text: str, history: list[dict] | None = None, monitor: bool = True,
        memory: list[str] | None = None) -> dict:
    from zenai.agents import conversation
    from zenai.agents.privacy import redact
    from zenai.models import fidelity
    from zenai.models.crisis import score_risk
    from zenai.models.distress import classify, which

    trace = []

    t = time.perf_counter()
    redacted = redact(text)
    n = len(re.findall(r"\[(EMAIL|PHONE|SSN|ID|URL|HANDLE)\]", redacted))
    trace.append(_stage("privacy", "done", _ms(t), f"{n} item(s) redacted" if n else "nothing identifying found"))

    t = time.perf_counter()
    risk = score_risk(redacted)
    escalate = risk >= settings.CRISIS_THRESHOLD
    trace.append(_stage("crisis", "escalated" if escalate else "done", _ms(t),
                        f"risk {risk:.2f} vs threshold {settings.CRISIS_THRESHOLD:.2f}"))
    if escalate:
        for s in ("mood", "memory", "conversation", "fidelity", "send"):
            trace.append(_stage(s, "skipped", detail="not run — the crisis rail stops the turn here"))
        out = {"escalate": True, "crisis_risk": risk, "redacted_text": redacted, "reply": None,
               "attempts": [], "trace": trace,
               "escalation": {"hotline": settings.CRISIS_HOTLINE, "campus": settings.CAMPUS_COUNSELING_NAME,
                              "phone": settings.CAMPUS_COUNSELING_PHONE or "NOT CONFIGURED",
                              "action": "human_handoff"},
               "note": "Crisis rail tripped. The language model never saw this message."}
        _log(out, monitor)
        return out

    t = time.perf_counter()
    dist = classify(redacted)
    mood = max(dist, key=dist.get)
    trace.append(_stage("mood", "done", _ms(t), f"{mood} {dist[mood]:.0%} · model: {which()}"))

    if memory:
        trace.append(_stage("memory", "done", None,
                            f"{len(memory)} note(s) the student chose to keep, from their own device"))
    else:
        trace.append(_stage("memory", "skipped",
                            detail="nothing saved: memory is off unless the student turns it on"))

    # draft -> check -> rewrite, at most MAX_REWRITES times
    attempts, feedback, reply, fallback = [], None, None, False
    t_draft = time.perf_counter()
    llm_ms = 0
    for i in range(1 + (settings.MAX_REWRITES if monitor else 0)):
        d = conversation.draft(redacted, history, mood.replace("_", " "), feedback, memory)
        llm_ms += d["ms"]
        if not monitor:
            attempts.append({"draft": d["text"], "checked": False})
            reply = d["text"]
            break
        chk = fidelity.verify(d["text"], second_opinion=settings.SECOND_OPINION)
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

    trace.append(_stage("conversation", "done", llm_ms,
                        f"{len(attempts)} draft(s) by {d['model']}"))
    if monitor:
        rejected = sum(1 for a in attempts if a.get("drift"))
        detail = ("first draft passed" if rejected == 0 else
                  f"{rejected} draft(s) rejected and rewritten" + (" · safe fallback used" if fallback else ""))
        trace.append(_stage("fidelity", "done", None, detail))
    else:
        trace.append(_stage("fidelity", "skipped", detail="monitor OFF — experiment E1 baseline"))
    trace.append(_stage("send", "done", None, "reply sent"))

    out = {"escalate": False, "crisis_risk": risk, "redacted_text": redacted, "distress": dist,
           "primary_emotion": mood, "reply": reply, "attempts": attempts, "fallback": fallback,
           "monitor": monitor, "trace": trace, "total_ms": _ms(t_draft)}
    _log(out, monitor)
    return out


def _log(out: dict, monitor: bool) -> None:
    """Redacted text only -- the raw message is never written anywhere."""
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a") as f:
            f.write(json.dumps({
                "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "monitor": monitor, "text": out["redacted_text"], "escalate": out["escalate"],
                "reply": out.get("reply"), "attempts": out.get("attempts", []),
                "fallback": out.get("fallback", False),
            }) + "\n")
    except OSError:
        pass
