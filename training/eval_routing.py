"""How often does the router pick the right specialist?

    python -m training.eval_routing

Two sets, both written by a model from one-line descriptions of each
specialist, WITHOUT seeing the router's cue lists or prompt:

    data/eval/routing_test_gpt.jsonl   100 msgs, 20/class, written by GPT (ChatGPT).
                                       The held-out TEST set: a different model
                                       from the Grok router, so it is not grading itself.
    data/eval/routing_dev_grok.jsonl   80 msgs, 16/class, written by Grok. Noisier:
                                       its "general" class includes school stress.

Scores the keyword rules and the model router on each. No mood nudge.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from zenai.agents.specialists import route, route_rules

CLASSES = ["academic", "stress_relief", "wellness", "referral", "general"]


def score(rows, router):
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(6) as ex:
        routed = list(ex.map(lambda r: router(r["text"]), rows))
    pairs = [(r["label"], x["id"] or "general") for r, x in zip(rows, routed)]
    conf = Counter(pairs)
    per = {}
    for c in CLASSES:
        tp = conf[(c, c)]
        fp = sum(conf[(g, c)] for g in CLASSES if g != c)
        fn = sum(conf[(c, p)] for p in CLASSES if p != c)
        pr = tp / (tp + fp) if tp + fp else 0.0
        rc = tp / (tp + fn) if tp + fn else 0.0
        per[c] = {"precision": round(pr, 3), "recall": round(rc, 3),
                  "f1": round(2 * pr * rc / (pr + rc), 3) if pr + rc else 0.0}
    acc = sum(g == p for g, p in pairs) / len(pairs)
    ms = [x.get("ms") for x in routed if x.get("ms")]
    return {"n": len(pairs), "fell_back_to_rules": sum(1 for x in routed if x.get("by") == "rules"),
           "median_ms": sorted(ms)[len(ms) // 2] if ms else None, "accuracy": round(acc, 3),
           "majority_baseline": round(max(Counter(g for g, _ in pairs).values()) / len(pairs), 3),
           "macro_f1": round(sum(v["f1"] for v in per.values()) / len(per), 3),
           "per_class": per,
           "confusion": {g: {p: conf[(g, p)] for p in CLASSES} for g in CLASSES},
           "misses": [{"text": r["text"], "gold": g, "routed": p}
                      for r, (g, p) in zip(rows, pairs) if g != p]}


def main() -> None:
    res = {}
    for name, path in [("test_gpt", "data/eval/routing_test_gpt.jsonl"),
                       ("dev_grok", "data/eval/routing_dev_grok.jsonl")]:
        rows = [json.loads(line) for line in Path(path).read_text().splitlines()]
        res[name] = {"rules": score(rows, route_rules), "model": score(rows, route)}
        for k, v in res[name].items():
            print(f"{name:9} {k:6} acc {v['accuracy']:.3f}  macro-F1 {v['macro_f1']:.3f}  "
                  f"median {v['median_ms']} ms  fallbacks {v['fell_back_to_rules']}")
    Path("results").mkdir(exist_ok=True)
    Path("results/routing_eval.json").write_text(json.dumps(res, indent=2))
    for m in res["test_gpt"]["model"]["misses"]:
        print(f'  {m["gold"]:>13} -> {m["routed"]:<13} {m["text"]}')


if __name__ == "__main__":
    main()
