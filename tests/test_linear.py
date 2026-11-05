"""The plain-Python models must give the same answers as scikit-learn."""

import pytest

from zenai.models.linear import LinearTextModel

pytest.importorskip("sklearn")
joblib = pytest.importorskip("joblib")

TEXTS = [
    "I have two midterms Friday and I keep thinking I'm not smart enough to be here",
    "You've got this! Try breaking your notes into 25-minute blocks.",
    "That sounds really hard. What matters most to you right now?",
    "honestly I don't know anymore, everything feels heavy",
    "ok",
    "",
]


@pytest.mark.parametrize("name", ["distress/tfidf", "fidelity/drift"])
def test_matches_sklearn(name):
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "models"
    if not (root / f"{name}.joblib").exists() or not (root / f"{name}.json.gz").exists():
        pytest.skip("models not present")
    ref = joblib.load(root / f"{name}.joblib")
    ours = LinearTextModel(root / f"{name}.json.gz")
    assert list(ours.classes_) == [str(c) for c in ref.classes_]
    for a, b in zip(ours.predict_proba(TEXTS), ref.predict_proba(TEXTS)):
        assert max(abs(x - float(y)) for x, y in zip(a, b)) < 1e-4
