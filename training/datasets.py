"""Load and prepare the training data.

Reads from data/raw/ on disk so training works offline, in CI, and on a machine
with nothing but scikit-learn and pandas installed. No `datasets` dependency,
no download at train time, and the demo cannot fail because HuggingFace is slow.

Fetch the raw files once:

    mkdir -p data/raw && cd data/raw
    for s in train validation test; do
      curl -sLO "https://huggingface.co/datasets/google-research-datasets/go_emotions/resolve/main/simplified/$s-00000-of-00001.parquet"
    done
    curl -sLO https://dl.fbaipublicfiles.com/parlai/empatheticdialogues/empatheticdialogues.tar.gz
    tar xzf empatheticdialogues.tar.gz
"""

from __future__ import annotations

import glob
from collections import Counter
from pathlib import Path

from training.taxonomy import (
    DISTRESS_CLASSES,
    EMPATHETIC_SUPPLEMENT,
    GOEMOTIONS_LABELS,
    map_goemotions,
)

RAW = Path("data/raw")


def _goemotions() -> tuple[list[str], list[str]]:
    import pandas as pd

    files = sorted(glob.glob(str(RAW / "*.parquet")))
    if not files:
        raise FileNotFoundError(
            f"No GoEmotions parquet in {RAW}/. See this module's docstring."
        )
    df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    texts, labels = [], []
    for text, ids in zip(df["text"], df["labels"]):
        names = [GOEMOTIONS_LABELS[int(i)] for i in ids]
        texts.append(text)
        labels.append(map_goemotions(names))
    return texts, labels


def _empathetic() -> tuple[list[str], list[str]]:
    """The supplement that fills the `overwhelm` and `isolation` gaps.

    ED carries a `context` column -- the situation label the speaker was given
    ("lonely", "anxious", "terrified"). GoEmotions has no equivalent for those
    two classes, which is why this exists. See taxonomy.GAPS.
    """
    import pandas as pd

    d = RAW / "empatheticdialogues"
    if not d.exists():
        return [], []
    texts, labels, seen = [], [], set()
    for f in ("train.csv", "valid.csv", "test.csv"):
        p = d / f
        if not p.exists():
            continue
        df = pd.read_csv(p, on_bad_lines="skip", engine="python", quoting=3)
        for ctx, utt in zip(df.get("context", []), df.get("utterance", [])):
            cls = EMPATHETIC_SUPPLEMENT.get(str(ctx).strip().lower())
            if not cls:
                continue
            u = str(utt).replace("_comma_", ",").strip()
            if len(u) < 12 or u in seen:
                continue
            seen.add(u)
            texts.append(u)
            labels.append(cls)
    return texts, labels


def load_distress_data(include_supplement: bool = True):
    """Return (texts, labels).

    include_supplement=False reproduces the GoEmotions-only baseline -- the
    ablation that shows what the two gap classes cost.
    """
    texts, labels = _goemotions()
    if include_supplement:
        t2, l2 = _empathetic()
        texts += t2
        labels += l2
    return texts, labels


def report(labels: list[str]) -> dict:
    """Class balance. Print this BEFORE training -- a neutral-heavy set gives a
    flattering accuracy number that means nothing, which is why we report
    macro-F1 per class instead."""
    c = Counter(labels)
    total = len(labels)
    return {
        "total": total,
        "per_class": {
            k: {"n": c[k], "pct": round(100 * c[k] / total, 1)} for k in DISTRESS_CLASSES
        },
    }


if __name__ == "__main__":
    import json

    for supp in (False, True):
        t, l = load_distress_data(include_supplement=supp)
        tag = "GoEmotions + EmpatheticDialogues" if supp else "GoEmotions only"
        print(f"\n=== {tag} ===")
        print(json.dumps(report(l), indent=2))
