"""Does the second opinion fix precision without giving up recall?

    python -m training.eval_judge --n 400

Measured on ESConv's HELD-OUT conversations -- the same group split the drift
detector was evaluated on, so none of these turns trained it -- against
ESConv's own human strategy labels:

    Providing Suggestions        -> advice
    Affirmation and Reassurance  -> reassurance

The same turns are scored two ways: the detector alone, and the detector plus
the second opinion on whatever it flags. Only flagged turns cost a model call.

CAVEAT, stated in the results: ESConv's reassurance label also covers healthy
validation ("that sounds hard"), which our protocol WANTS. So for reassurance,
some of what the second opinion "loses" against ESConv's labels is the second
opinion being right by our protocol. Advice is the clean comparison.

Also re-checks every draft the Oct 15 pilot rejected.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from training.train_drift import load

MOVES = ["advice", "reassurance"]


def prf(pred, gold):
    tp = sum(p and g for p, g in zip(pred, gold))
    fp = sum(p and not g for p, g in zip(pred, gold))
    fn = sum(g and not p for p, g in zip(pred, gold))
    pr = tp / (tp + fp) if tp + fp else 0.0
    rc = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * pr * rc / (pr + rc) if pr + rc else 0.0
    return {"precision": round(pr, 3), "recall": round(rc, 3), "f1": round(f1, 3),
            "flagged": tp + fp, "true_positives": tp, "false_alarms": fp, "missed": fn}


def main() -> None:
    from sklearn.model_selection import GroupShuffleSplit

    from zenai.models import fidelity

    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=400)
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()

    texts, labels, groups = load()
    _, te = next(GroupShuffleSplit(n_splits=1, test_size=0.15, random_state=42)
                 .split(texts, labels, groups))
    rng = random.Random(3)
    idx = rng.sample(list(te), min(a.n, len(te)))
    X = [texts[i] for i in idx]
    gold = {mv: [labels[i] == mv for i in idx] for mv in MOVES}

    det = [fidelity.check(t) for t in X]
    det_pred = {mv: [d["moves"][mv]["flagged"] for d in det] for mv in MOVES}

    def judged(k):
        if not det[k]["drift"]:
            return det[k]           # nothing flagged: the second opinion is never called
        return fidelity.verify(X[k])

    with ThreadPoolExecutor(a.workers) as ex:
        full = list(ex.map(judged, range(len(X))))
    full_pred = {mv: [f["moves"][mv]["flagged"] for f in full] for mv in MOVES}
    calls = sum(1 for f in full if f.get("judge", {}).get("ran"))
    errors = sum(1 for f in full if f.get("judge", {}).get("error"))

    res = {"data": "ESConv held-out conversations (group split, seed 42), random sample",
           "n_turns": len(X), "second_opinion_calls": calls, "second_opinion_errors": errors,
           "detector_alone": {mv: prf(det_pred[mv], gold[mv]) for mv in MOVES},
           "detector_plus_second_opinion": {mv: prf(full_pred[mv], gold[mv]) for mv in MOVES},
           "caveat": "ESConv's reassurance label includes validation our protocol wants; "
                     "advice is the clean comparison."}

    # ---- the drafts the Oct 15 pilot rejected ----
    rej = Path("results/e1/pilot-v0/audit_rejected.csv")
    if rej.exists():
        drafts = sorted({r["rejected_draft"] for r in csv.DictReader(rej.open())})
        with ThreadPoolExecutor(a.workers) as ex:
            again = list(ex.map(fidelity.verify, drafts))
        res["pilot_rejections_rechecked"] = {
            "drafts": len(drafts),
            "still_rejected": sum(1 for r in again if r["drift"]),
            "now_pass": sum(1 for r in again if not r["drift"]),
            "examples_now_pass": [d for d, r in zip(drafts, again) if not r["drift"]][:5],
            "examples_still_rejected": [
                {"draft": d, "moves": [m for m, v in r["moves"].items() if v.get("flagged")]}
                for d, r in zip(drafts, again) if r["drift"]][:5],
        }

    Path("results").mkdir(exist_ok=True)
    Path("results/judge_eval.json").write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
