"""Load and prepare the training data.

Every dataset here was verified live on HuggingFace on 2026-09-30.
Nothing is downloaded at import time -- call the functions.
"""

from __future__ import annotations

from collections import Counter

from training.taxonomy import (
    DISTRESS_CLASSES,
    EMPATHETIC_SUPPLEMENT,
    map_goemotions,
)

GOEMOTIONS = "google-research-datasets/go_emotions"
EMPATHETIC = "facebook/empathetic_dialogues"
EMOTION_6 = "dair-ai/emotion"


def load_distress_data(include_supplement: bool = True):
    """Return (texts, labels) for the distress classifier.

    include_supplement=False reproduces the GoEmotions-only baseline, which is
    the ablation worth reporting: it shows what the two gap classes cost.
    """
    from datasets import load_dataset

    ds = load_dataset(GOEMOTIONS, "simplified")
    names = ds["train"].features["labels"].feature.names

    texts: list[str] = []
    labels: list[str] = []
    for split in ("train", "validation", "test"):
        for row in ds[split]:
            texts.append(row["text"])
            labels.append(map_goemotions([names[i] for i in row["labels"]]))

    if include_supplement:
        ed = load_dataset(EMPATHETIC)
        seen: set[str] = set()
        for split in ed:
            for row in ed[split]:
                ctx = (row.get("context") or "").lower()
                cls = EMPATHETIC_SUPPLEMENT.get(ctx)
                utt = row.get("utterance") or ""
                if cls and utt and utt not in seen:
                    seen.add(utt)
                    texts.append(utt)
                    labels.append(cls)

    return texts, labels


def report(labels: list[str]) -> dict:
    """Class balance. Print this BEFORE training -- an 80% neutral set will
    give you a flattering accuracy number that means nothing, which is exactly
    why we report macro-F1 per class instead."""
    c = Counter(labels)
    total = len(labels)
    return {
        "total": total,
        "per_class": {k: {"n": c[k], "pct": round(100 * c[k] / total, 1)} for k in DISTRESS_CLASSES},
    }


if __name__ == "__main__":
    import json

    texts, labels = load_distress_data()
    print(json.dumps(report(labels), indent=2))
    print(f"\nexample: {texts[0]!r} -> {labels[0]}")
