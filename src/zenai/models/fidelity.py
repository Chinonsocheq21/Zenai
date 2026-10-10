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
