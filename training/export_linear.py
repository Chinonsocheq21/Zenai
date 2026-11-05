"""Export the two runtime models to plain numbers for zenai.models.linear.

    python -m training.export_linear

models/distress/tfidf.joblib -> models/distress/tfidf.json.gz
models/fidelity/drift.joblib -> models/fidelity/drift.json.gz

Run it again after retraining either model.
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import joblib

PAIRS = [("models/distress/tfidf.joblib", "models/distress/tfidf.json.gz"),
         ("models/fidelity/drift.joblib", "models/fidelity/drift.json.gz")]


def export(src: str, dst: str) -> None:
    pipe = joblib.load(src)
    vec, lr = pipe.steps[0][1], pipe.steps[-1][1]
    assert vec.analyzer == "word" and vec.lowercase and vec.norm == "l2" and vec.use_idf
    assert vec.token_pattern == r"(?u)\b\w\w+\b" and vec.preprocessor is None and vec.tokenizer is None
    d = {"classes": [str(c) for c in lr.classes_],
         "vocab": {k: int(v) for k, v in vec.vocabulary_.items()},
         "idf": [round(float(v), 7) for v in vec.idf_],
         "coef": [[round(float(v), 7) for v in row] for row in lr.coef_],
         "intercept": [float(v) for v in lr.intercept_],
         "sublinear_tf": bool(vec.sublinear_tf), "ngram_range": list(vec.ngram_range)}
    Path(dst).write_bytes(gzip.compress(json.dumps(d, separators=(",", ":")).encode(), 9))
    print(dst, round(Path(dst).stat().st_size / 1e6, 2), "MB")


if __name__ == "__main__":
    for s, t in PAIRS:
        export(s, t)
