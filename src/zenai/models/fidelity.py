"""The Fidelity Monitor's drift detector. Loads once, lazily.

Scores a CANDIDATE REPLY -- before any student sees it -- for the moves a
counselor is taught not to make. Trained by `python -m training.train_drift`
on ESConv; see that module for the data, the split and the gaps.

Scored sentence by sentence, and a move is flagged if ANY sentence makes it.
A reply like "You've got this! Try breaking your notes into blocks." carries
two moves in two sentences; scored whole, they blur and neither clears its
threshold. Measured on held-out conversations, sentence-level scoring keeps
the same precision/recall trade-off, so this costs nothing and catches the
mixed replies a language model actually writes.

Thresholds were chosen on held-out conversations, leaning toward recall: a
false flag costs one extra regeneration, a miss puts drift in front of a
student.

    advice       >= 0.40   recall 0.77  precision 0.41
    reassurance  >= 0.45   recall 0.60  precision 0.34

Diagnosis is NOT detected yet -- there is no labelled data for it. It is
reported as such rather than silently treated as clear.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

MODEL = Path(__file__).resolve().parents[3] / "models" / "fidelity" / "drift.joblib"
THRESHOLDS = {"advice": 0.40, "reassurance": 0.45}
_SENT = re.compile(r"(?<=[.!?])\s+")


@lru_cache(maxsize=1)
def _model():
    if not MODEL.exists():
        raise RuntimeError(f"No drift detector at {MODEL}. Run: python -m training.train_drift")
    import joblib

    return joblib.load(MODEL)


def available() -> bool:
    return MODEL.exists()


def sentences(text: str) -> list[str]:
    parts = [s.strip() for s in _SENT.split(text.strip()) if len(s.strip()) > 3]
    return parts or [text.strip()]


def check(reply: str) -> dict:
    """{"drift": bool, "moves": {...}, "sentences": [...]} for one candidate reply."""
    m = _model()
    sents = sentences(reply)
    probs = m.predict_proba(sents)
    cls = list(m.classes_)

    moves = {}
    for move, th in THRESHOLDS.items():
        i = cls.index(move)
        j = int(probs[:, i].argmax())
        score = float(probs[j, i])
        moves[move] = {
            "score": round(score, 3),
            "threshold": th,
            "flagged": score >= th,
            "sentence": sents[j],
        }
    moves["diagnosis"] = {
        "score": None, "threshold": None, "flagged": False, "sentence": None,
        "status": "not detected yet — no labelled data; needs examples written "
                  "against the ACT/CBT protocol",
    }
    per_sentence = [
        {"text": s, **{mv: round(float(probs[k, cls.index(mv)]), 3) for mv in THRESHOLDS}}
        for k, s in enumerate(sents)
    ]
    return {
        "drift": any(v["flagged"] for v in moves.values()),
        "moves": moves,
        "sentences": per_sentence,
        "verdict": "rejected — would be regenerated" if any(v["flagged"] for v in moves.values())
                   else "passes — would be sent",
    }


def verify(reply: str, second_opinion: bool = True) -> dict:
    """The Fidelity Monitor as the turn uses it: the detector, then -- only for
    what it flags, or when the draft names a condition -- a second opinion from
    the language model (see zenai.models.judge).

    Same shape as check(), plus per move `detector_flagged` and `overturned`, and
    a `judge` record. Every sentence over a move's threshold is judged, not only
    the strongest one, so a confirmed second instance still counts.
    """
    r = check(reply)
    from zenai import llm
    from zenai.models import judge

    suspects, sid = [], 1
    for s in r["sentences"]:
        for mv, th in THRESHOLDS.items():
            if s[mv] >= th:
                suspects.append({"id": sid, "sentence": s["text"], "move": mv, "score": s[mv]})
                sid += 1
    needs_judge = bool(suspects) or judge.mentions_condition(reply)
    for mv in THRESHOLDS:
        r["moves"][mv]["detector_flagged"] = r["moves"][mv]["flagged"]
        r["moves"][mv]["overturned"] = False

    if not (second_opinion and needs_judge and llm.available()):
        r["judge"] = {"ran": False}
        if needs_judge and not suspects:   # names a condition, but no judge to confirm it
            r["moves"]["diagnosis"]["status"] = "possible diagnosis wording; no second opinion available"
        return r

    v = judge.review(reply, suspects)
    confirmed = {it.get("id"): bool(it.get("confirmed")) for it in v.get("items", [])}
    for mv in THRESHOLDS:
        mine = [s for s in suspects if s["move"] == mv]
        if not mine:
            continue
        kept = [s for s in mine if confirmed.get(s["id"], True)]   # missing verdict = keep (fail closed)
        if kept:
            best = max(kept, key=lambda s: s["score"])
            r["moves"][mv].update(flagged=True, sentence=best["sentence"], score=round(best["score"], 3))
        else:
            r["moves"][mv].update(flagged=False, overturned=True)
    dx = v.get("diagnosis") or {}
    r["moves"]["diagnosis"] = {
        "score": None, "threshold": None, "flagged": bool(dx.get("present")),
        "sentence": dx.get("sentence"), "status": "checked by second opinion",
    }
    r["judge"] = {"ran": True, "ms": v.get("ms"), "error": v.get("error"),
                  "items": [{**s, "confirmed": confirmed.get(s["id"], True)} for s in suspects]}
    r["drift"] = any(m.get("flagged") for m in r["moves"].values())
    r["verdict"] = "rejected — would be regenerated" if r["drift"] else "passes — would be sent"
    return r
