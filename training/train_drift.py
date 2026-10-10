"""The drift detector -- the first trained half of the Fidelity Monitor.

    python -m training.train_drift

WHAT IT DETECTS. Two of the three moves a counselor is taught not to make,
in a candidate reply, before the student sees it:

    advice        "Try breaking your notes into 25-minute blocks."
    reassurance   "Don't worry, you'll do great!"

The third, diagnosis ("sounds like test anxiety"), has no labelled source and
waits for the protocol rubric -- see GAPS below.

THE DATA. ESConv (Liu et al., 2021): 1,300 emotional-support conversations in
which every supporter turn is annotated with the strategy it uses. Two of its
eight strategies are exactly our two moves:

    Providing Suggestions          -> advice
    Affirmation and Reassurance    -> reassurance
    the other six                  -> other

HOW IT IS SPLIT, and why it matters. By CONVERSATION, not by turn. Turns from
one conversation share a topic and a writer; split them at random and the same
conversation lands in both train and test, so the model is graded partly on
text it has effectively seen. We train both ways and report the gap, so the
number on the slide is the honest one.

GAPS -- say these out loud.
  * ESConv is PEER support, where suggestions are often welcome. The detector
    finds the MOVE; it is ZenAI's protocol that calls the move drift.
  * "Affirmation and Reassurance" mixes validation ("that sounds hard") with
    false reassurance ("you'll be fine"). Only the second is drift, so this
    label over-flags. Expect reassurance precision to be the weak number.
  * Diagnosis has no labelled data at all. It needs hand-labelled examples
    against Joseph's written protocol.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

RAW = Path("data/raw/ESConv.json")
OUT = Path("models/fidelity")
RESULTS = Path("results")

STRATEGY_TO_MOVE = {
    "Providing Suggestions": "advice",
    "Affirmation and Reassurance": "reassurance",
}
MOVES = ["advice", "reassurance", "other"]


def load() -> tuple[list[str], list[str], list[int]]:
    """Supporter turns, their move label, and which conversation each came from."""
    if not RAW.exists():
        raise FileNotFoundError(
            f"{RAW} not found. Fetch it once:\n  curl -sL -o {RAW} "
            "https://huggingface.co/datasets/thu-coai/esconv/resolve/main/ESConv.json"
        )
    convs = json.loads(RAW.read_text())
    texts, labels, groups = [], [], []
    for ci, conv in enumerate(convs):
        for turn in conv["dialog"]:
            if turn["speaker"] != "supporter":
                continue
            text = (turn.get("content") or "").strip()
            strategy = (turn.get("annotation") or {}).get("strategy")
            if len(text) < 6 or not strategy:
                continue
            texts.append(text)
            labels.append(STRATEGY_TO_MOVE.get(strategy, "other"))
            groups.append(ci)
    return texts, labels, groups


def _pipeline():
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline

    return make_pipeline(
        TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True, max_features=60_000),
        LogisticRegression(max_iter=2000, class_weight="balanced"),
    )


def _score(y_true, y_pred) -> dict:
    from sklearn.metrics import classification_report, confusion_matrix

    rep = classification_report(y_true, y_pred, labels=MOVES, output_dict=True, zero_division=0)
    return {
        "macro_f1": round(rep["macro avg"]["f1-score"], 3),
        "per_class": {m: {k: round(rep[m][k], 3) for k in ("precision", "recall", "f1-score")}
                      | {"n": int(rep[m]["support"])} for m in MOVES},
        "confusion": confusion_matrix(y_true, y_pred, labels=MOVES).tolist(),
    }


def main() -> None:
    import joblib
    from sklearn.model_selection import GroupShuffleSplit, train_test_split

    texts, labels, groups = load()
    bal = Counter(labels)
    print(f"{len(texts)} supporter turns from {len(set(groups))} conversations")
    print("  " + "  ·  ".join(f"{m} {bal[m]} ({100 * bal[m] / len(labels):.0f}%)" for m in MOVES))

    # --- the honest split: whole conversations held out ---
    gss = GroupShuffleSplit(n_splits=1, test_size=0.15, random_state=42)
    tr, te = next(gss.split(texts, labels, groups))
    Xtr, Xte = [texts[i] for i in tr], [texts[i] for i in te]
    ytr, yte = [labels[i] for i in tr], [labels[i] for i in te]
    assert not {groups[i] for i in tr} & {groups[i] for i in te}, "conversation leak"

    pipe = _pipeline().fit(Xtr, ytr)
    grouped = _score(yte, pipe.predict(Xte))

    majority = max(set(ytr), key=ytr.count)
    baseline = _score(yte, [majority] * len(yte))

    # --- the leaky split, ONLY to measure how much leakage would have flattered us ---
    Xa, Xb, ya, yb = train_test_split(texts, labels, test_size=0.15, random_state=42,
                                      stratify=labels)
    leaky = _score(yb, _pipeline().fit(Xa, ya).predict(Xb))

    print(f"\nmajority baseline ('{majority}')   macro-F1 {baseline['macro_f1']:.3f}")
    print(f"drift detector, split by conversation  macro-F1 {grouped['macro_f1']:.3f}   <- reported")
    print(f"same model, split by turn (leaky)      macro-F1 {leaky['macro_f1']:.3f}   "
          f"(+{leaky['macro_f1'] - grouped['macro_f1']:.3f} of flattery)")
    print()
    for m in MOVES:
        r = grouped["per_class"][m]
        print(f"  {m:12s} P {r['precision']:.2f}  R {r['recall']:.2f}  F1 {r['f1-score']:.2f}   n={r['n']}")

    OUT.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, OUT / "drift.joblib")
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "drift_detector.json").write_text(json.dumps({
        "data": "ESConv supporter turns",
        "n_turns": len(texts), "n_conversations": len(set(groups)),
        "label_balance": dict(bal),
        "split": "GroupShuffleSplit by conversation, 15% held out",
        "n_train": len(Xtr), "n_test": len(Xte),
        "model": "tfidf(1-2gram, sublinear) + logistic regression, class-balanced",
        "majority_baseline": baseline,
        "grouped": grouped,
        "leaky_turn_split_for_comparison_only": leaky,
    }, indent=2))
    print(f"\nwrote {OUT / 'drift.joblib'} and {RESULTS / 'drift_detector.json'}")


if __name__ == "__main__":
    main()
