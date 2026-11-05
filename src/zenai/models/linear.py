"""TF-IDF + logistic regression, without scikit-learn.

Both runtime models (distress, drift) are a TfidfVectorizer followed by a
LogisticRegression. Running them only needs the vocabulary, the idf weights and
the coefficients, so `training/export_linear.py` writes those to a small
.json.gz and this file does the arithmetic in plain Python. That keeps scipy
and scikit-learn (about 200 MB) out of the hosted server.

It mirrors scikit-learn exactly for the settings we use: lowercase, token
pattern (?u)\\b\\w\\w+\\b, word 1-2 grams joined by a space, optional sublinear
tf, smooth idf, l2 norm; then sigmoid for two classes or softmax for more.
tests/test_linear.py checks the probabilities match scikit-learn's.
"""

from __future__ import annotations

import gzip
import json
import math
import re
from collections import Counter
from pathlib import Path

TOKEN = re.compile(r"(?u)\b\w\w+\b")


class LinearTextModel:
    def __init__(self, path: Path):
        d = json.loads(gzip.decompress(Path(path).read_bytes()))
        self.classes_ = d["classes"]
        self.vocab: dict[str, int] = d["vocab"]
        self.idf: list[float] = d["idf"]
        self.coef: list[list[float]] = d["coef"]
        self.intercept: list[float] = d["intercept"]
        self.sublinear = d["sublinear_tf"]
        self.ngram = tuple(d["ngram_range"])

    def _features(self, text: str) -> dict[int, float]:
        toks = TOKEN.findall(text.lower())
        grams: list[str] = []
        lo, hi = self.ngram
        for n in range(lo, hi + 1):
            grams += [" ".join(toks[i:i + n]) for i in range(len(toks) - n + 1)]
        counts = Counter(g for g in grams if g in self.vocab)
        x = {}
        for g, c in counts.items():
            tf = 1.0 + math.log(c) if self.sublinear else float(c)
            x[self.vocab[g]] = tf * self.idf[self.vocab[g]]
        norm = math.sqrt(sum(v * v for v in x.values()))
        return {k: v / norm for k, v in x.items()} if norm else x

    def predict_proba(self, texts: list[str]) -> list[list[float]]:
        out = []
        for t in texts:
            x = self._features(t)
            z = [b + sum(w[k] * v for k, v in x.items()) for w, b in zip(self.coef, self.intercept)]
            if len(z) == 1:                       # two classes: one score, sigmoid
                p = 1.0 / (1.0 + math.exp(-z[0]))
                out.append([1.0 - p, p])
            else:                                 # several classes: softmax
                m = max(z)
                e = [math.exp(v - m) for v in z]
                s = sum(e)
                out.append([v / s for v in e])
        return out
