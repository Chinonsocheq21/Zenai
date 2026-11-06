"""The plain-Python models must give the same answers as scikit-learn.

The first test trains small pipelines with the same settings as the real models,
exports them with training.export_linear and compares, so it runs anywhere
scikit-learn is installed (CI installs it for this). The second compares the real
models too, when their .joblib originals are on disk (they are not committed).
"""

from pathlib import Path

import pytest

from zenai.models.linear import LinearTextModel

sklearn = pytest.importorskip("sklearn")
joblib = pytest.importorskip("joblib")

TEXTS = [
    "I have two midterms Friday and I keep thinking I'm not smart enough to be here",
    "You've got this! Try breaking your notes into 25-minute blocks.",
    "That sounds really hard. What matters most to you right now?",
    "honestly I don't know anymore, everything feels heavy heavy heavy",
    "ok",
    "",
]
TRAIN = [
    ("try making a study plan tonight", "advice"), ("you should talk to your professor", "advice"),
    ("you'll be fine, don't worry", "reassurance"), ("you've got this, it will work out", "reassurance"),
    ("that sounds really hard", "other"), ("what matters most to you right now", "other"),
    ("try a short walk before you study", "advice"), ("everything will be okay, you'll do great", "reassurance"),
    ("it makes sense you feel that way", "other"), ("you keep opening your notes and closing them", "other"),
]


def _fit(classes: int, sublinear: bool):
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline

    rows = TRAIN if classes > 2 else [(t, "drift" if y != "other" else "other") for t, y in TRAIN]
    pipe = make_pipeline(TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=sublinear),
                         LogisticRegression(class_weight="balanced"))
    pipe.fit([t for t, _ in rows], [y for _, y in rows])
    return pipe


def _same(ours, ref):
    assert list(ours.classes_) == [str(c) for c in ref.classes_]
    for a, b in zip(ours.predict_proba(TEXTS), ref.predict_proba(TEXTS)):
        assert max(abs(x - float(y)) for x, y in zip(a, b)) < 1e-4


@pytest.mark.parametrize("classes,sublinear", [(3, True), (3, False), (2, True), (2, False)])
def test_matches_sklearn_on_fresh_models(tmp_path, classes, sublinear):
    from training.export_linear import export

    ref = _fit(classes, sublinear)
    joblib.dump(ref, tmp_path / "m.joblib")
    export(str(tmp_path / "m.joblib"), str(tmp_path / "m.json.gz"))
    _same(LinearTextModel(tmp_path / "m.json.gz"), ref)


@pytest.mark.parametrize("name", ["distress/tfidf", "fidelity/drift"])
def test_matches_sklearn_on_the_real_models(name):
    root = Path(__file__).resolve().parents[1] / "models"
    if not (root / f"{name}.joblib").exists():
        pytest.skip("the .joblib originals are not committed; run locally after training")
    _same(LinearTextModel(root / f"{name}.json.gz"), joblib.load(root / f"{name}.joblib"))
