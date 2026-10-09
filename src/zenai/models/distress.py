"""Inference for Model 1, the distress classifier. Loads once, lazily.

Serves whichever trained model exists, best first:

  1. a fine-tuned transformer in models/distress/      (config.json present)
  2. the TF-IDF + logistic-regression pipeline          (tfidf.joblib)

Train either with `python -m training.train_distress [--baseline]`.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

# repo/src/zenai/models/distress.py -> repo/models/distress, wherever we run from
MODEL_DIR = Path(__file__).resolve().parents[3] / "models" / "distress"
TFIDF = MODEL_DIR / "tfidf.joblib"


@lru_cache(maxsize=1)
def _model():
    if (MODEL_DIR / "config.json").exists():
        from transformers import pipeline

        return "transformer", pipeline(
            "text-classification", model=str(MODEL_DIR), tokenizer=str(MODEL_DIR), top_k=None
        )
    if TFIDF.exists():
        import joblib

        return "tfidf", joblib.load(TFIDF)
    raise RuntimeError(
        f"No trained distress model in {MODEL_DIR}. "
        "Run: python -m training.train_distress --baseline"
    )


def which() -> str:
    """Which model is being served -- for /health and for honesty in the demo."""
    return _model()[0]


def classify(text: str) -> dict[str, float]:
    """Full distribution over the six distress classes, not just the argmax --
    Mood Check-In and Progress both want the shape."""
    kind, m = _model()
    if kind == "tfidf":
        probs = m.predict_proba([text])[0]
        return {str(c): round(float(p), 4) for c, p in zip(m.classes_, probs)}
    return {s["label"]: round(float(s["score"]), 4) for s in m(text)[0]}
