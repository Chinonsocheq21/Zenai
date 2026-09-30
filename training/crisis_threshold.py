"""Model 2's operating point -- the deliberate recall/precision trade.

This module exists to make ONE argument, and it is the argument that turns a
70% project into a 90% one:

    A missed crisis and a false alarm are not the same kind of error.
    So we do not pick the threshold that maximises accuracy or F1.
    We pick the lowest threshold whose false-alarm rate is still tolerable,
    and we say what we paid for it.

Produces the sweep table and the curve that go on the midterm slide.
"""

from __future__ import annotations

import numpy as np
from sklearn.metrics import confusion_matrix


def sweep(y_true, y_prob, thresholds=None) -> list[dict]:
    if thresholds is None:
        thresholds = np.arange(0.05, 0.96, 0.05)
    rows = []
    for t in thresholds:
        pred = (np.asarray(y_prob) >= t).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_true, pred, labels=[0, 1]).ravel()
        rows.append({
            "threshold": round(float(t), 2),
            "recall": round(tp / (tp + fn), 3) if (tp + fn) else 0.0,
            "precision": round(tp / (tp + fp), 3) if (tp + fp) else 0.0,
            "missed_crises": int(fn),          # the number that actually matters
            "false_alarms": int(fp),
            "tp": int(tp), "tn": int(tn),
        })
    return rows


def choose(rows: list[dict], min_recall: float = 0.95) -> dict:
    """Highest threshold that still clears min_recall.

    Recall is the constraint, not the objective. We take the most precise model
    among those that are safe enough, rather than the most accurate overall.
    """
    ok = [r for r in rows if r["recall"] >= min_recall]
    if not ok:
        best = max(rows, key=lambda r: r["recall"])
        return {**best, "warning": f"no threshold reaches recall {min_recall}; "
                                   f"best is {best['recall']}. Say this out loud."}
    return max(ok, key=lambda r: r["threshold"])


def explain(chosen: dict, min_recall: float = 0.95) -> str:
    """The sentence to say in the presentation."""
    return (
        f"We set the crisis threshold at {chosen['threshold']} rather than 0.5. "
        f"That catches {chosen['recall']:.0%} of flagged turns "
        f"({chosen['missed_crises']} missed on the test set) at a precision of "
        f"{chosen['precision']:.0%} — {chosen['false_alarms']} false alarms. "
        f"We chose recall deliberately: an unnecessary escalation costs a student "
        f"one awkward message, a missed one costs something we are not willing to risk."
    )
