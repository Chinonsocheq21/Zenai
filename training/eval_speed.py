"""Can a faster model write the drafts without drifting more?

    python -m training.eval_speed --n 40

Same 40 ESConv situations as the E1 pilot (seed 7), each run through the full
turn (monitor ON) with two draft models. The Fidelity Monitor and its second
opinion stay on grok-4.3 for both, so the judge is held constant. Reports:

  first_draft_drift  share of first drafts the monitor rejected (lower = model
                     follows the protocol better on its own)
  fallback           share of turns where every rewrite drifted
  latency            whole turn, wall clock, median and 90th percentile

The replies are saved so a person can read them side by side.
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from training.e1 import sample_messages

MODELS = ["grok-4.3", "grok-4.20-0309-non-reasoning"]


def run_one(text: str) -> dict:
    from zenai.agents import turn

    t = time.perf_counter()
    r = turn.run(text, monitor=True, client="eval")
    return {"ms": round((time.perf_counter() - t) * 1000), "escalate": r["escalate"], "reply": r.get("reply"),
            "first_drift": bool(r["attempts"] and r["attempts"][0].get("drift")),
            "drafts": len(r["attempts"]), "fallback": r.get("fallback", False),
            "first_draft": r["attempts"][0]["draft"] if r["attempts"] else None}


def pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * len(xs)))]


def main() -> None:
    from zenai.config import settings

    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=40)
    a = ap.parse_args()
    msgs = [m["text"] for m in sample_messages(a.n)]
    res, rows = {}, {}
    for model in MODELS:
        settings.DRAFT_MODEL = model
        with ThreadPoolExecutor(4) as ex:
            out = list(ex.map(run_one, msgs))
        ok = [o for o in out if not o["escalate"]]
        ms = [o["ms"] for o in ok]
        res[model] = {"turns": len(ok), "crisis_excluded": len(out) - len(ok),
                      "first_draft_drift": round(sum(o["first_drift"] for o in ok) / len(ok), 3),
                      "fallback": round(sum(o["fallback"] for o in ok) / len(ok), 3),
                      "mean_drafts": round(statistics.mean(o["drafts"] for o in ok), 2),
                      "latency_median_ms": statistics.median(ms), "latency_p90_ms": pct(ms, 0.9)}
        rows[model] = out
        print(model, json.dumps(res[model]))
    Path("results").mkdir(exist_ok=True)
    Path("results/speed_eval.json").write_text(json.dumps(
        {"n_messages": len(msgs), "judge_model": settings.JUDGE_MODEL, "results": res,
         "side_by_side": [{"message": m, **{k: rows[k][i]["reply"] for k in MODELS}} for i, m in enumerate(msgs)]},
        indent=2))


if __name__ == "__main__":
    main()
