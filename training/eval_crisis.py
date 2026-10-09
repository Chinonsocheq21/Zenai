"""Evaluate the crisis detector and choose its operating point.

    .venv/bin/python -m training.eval_crisis data/crisis_eval.csv

The CSV needs two columns: `text` and `label` (1 = should escalate, 0 = should not).

WHAT THIS IS FOR, and the argument it exists to make:

    A missed crisis and a false alarm are not the same kind of error.
    So we do not pick the threshold that maximises accuracy or F1.
    We pick the loosest threshold whose false-alarm rate is still tolerable,
    and we state what precision we paid for it.

That asymmetry is the whole point, and `explain()` writes the sentence for the
slide.

ON THE DATA -- read this before quoting any number this produces.

There is no freely available labelled crisis corpus. The ones that exist
(CLPsych and similar) are access-controlled, and that restriction is correct
rather than an obstacle. So:

  * `data/crisis_eval_example.csv` is a SMOKE TEST. It exists to prove the
    harness runs end to end. It is a handful of synthetic lines written to
    exercise the code paths. Numbers from it are NOT a result and must never
    appear on a slide as one.
  * A real evaluation needs a real annotated set, which in practice means a
    data-use agreement, or a set annotated by people qualified to annotate it.
    Saying that plainly in the presentation is a stronger answer than a
    classifier trained on a weak proxy.

Owner: Abraham.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from training.crisis_threshold import choose, explain, sweep

sys.path.insert(0, "src")


def load(path: str) -> tuple[list[str], list[int]]:
    texts, labels = [], []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            t = (row.get("text") or "").strip()
            if not t or t.startswith("#"):
                continue
            texts.append(t)
            labels.append(int(row["label"]))
    return texts, labels


def main(path: str, min_recall: float = 0.95) -> None:
    from zenai.models.crisis import score_risk

    texts, y = load(path)
    probs = [score_risk(t) for t in texts]
    n_pos = sum(y)
    print(f"{len(texts)} examples · {n_pos} positive · {len(texts) - n_pos} negative\n")

    rows = sweep(y, probs)
    print(f"{'thresh':>7}  {'recall':>7}  {'prec':>7}  {'missed':>7}  {'false alarms':>13}")
    for r in rows:
        print(f"{r['threshold']:>7}  {r['recall']:>7}  {r['precision']:>7}"
              f"  {r['missed_crises']:>7}  {r['false_alarms']:>13}")

    chosen = choose(rows, min_recall)
    print("\nCHOSEN OPERATING POINT")
    print(json.dumps(chosen, indent=2))
    print("\nThe sentence for the slide:\n")
    print("  " + explain(chosen, min_recall))

    out = Path("results/crisis_threshold.json")
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(
        {"source": path, "n": len(texts), "n_positive": n_pos,
         "min_recall": min_recall, "sweep": rows, "chosen": chosen,
         "caveat": ("Numbers from crisis_eval_example.csv are a SMOKE TEST, not a "
                    "result. See the module docstring.")},
        indent=2))
    print(f"\nwrote {out}")

    if "example" in path:
        print("\n" + "!" * 72)
        print("! This ran on the SMOKE TEST file. These numbers are not a result and")
        print("! must not go on a slide. See training/eval_crisis.py for why.")
        print("!" * 72)


if __name__ == "__main__":
    args = sys.argv[1:]
    main(args[0] if args else "data/crisis_eval_example.csv",
         float(args[1]) if len(args) > 1 else 0.95)
