"""Model 1 -- the distress classifier. THE MIDTERM DELIVERABLE.

Two models, both reported:
  baseline  TF-IDF + logistic regression   (seconds, CPU)
  main      distilroberta-base fine-tune   (~15 min, CPU; minutes on GPU)

Report MACRO-F1, not accuracy. The class balance is skewed toward neutral, so
accuracy flatters and says nothing. Print the per-class table and the confusion
matrix -- the weak classes (see taxonomy.GAPS) are a finding, not a failure.

    python -m training.train_distress --baseline      # start here, today
    python -m training.train_distress                 # the real one
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

from training.datasets import load_distress_data, report
from training.taxonomy import DISTRESS_CLASSES

OUT = Path("models/distress")


def run_baseline(X_tr, y_tr, X_te, y_te) -> dict:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline

    pipe = make_pipeline(
        TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=50_000),
        LogisticRegression(max_iter=1000, class_weight="balanced"),
    )
    pipe.fit(X_tr, y_tr)
    pred = pipe.predict(X_te)
    return {
        "model": "tfidf+logreg",
        "report": classification_report(
            y_te, pred, labels=DISTRESS_CLASSES, output_dict=True, zero_division=0
        ),
        "confusion": confusion_matrix(y_te, pred, labels=DISTRESS_CLASSES).tolist(),
    }


def run_transformer(X_tr, y_tr, X_te, y_te, epochs: int = 2,
                    max_len: int = 64, batch: int = 16) -> dict:
    """Fine-tune distilroberta.

    Three choices here are what make this finish in half an hour instead of a
    day and a half, on this laptop:

      * Apple GPU (MPS) when it exists. Measured on this machine, batch 32:
        CPU 3.13 s/step, MPS 0.42 s/step -- 7.5x.
      * max_length 64, not 128. These are Reddit comments and single chat
        utterances; 128 doubles the cost and buys nothing. MPS at 128 was
        1.44 s/step.
      * dynamic padding -- pad each batch to ITS longest sequence rather than
        to max_len. Most of this corpus is far shorter than 64.

    MPS memory is the laptop's UNIFIED memory, shared with everything else
    running. batch 32 OOMs at ~6.8 GB when a browser is open. batch 16 is the
    safe default here; drop to 8 if it still dies. Do NOT reach for
    PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0 -- that removes the guard rail and can
    take the whole machine down.
    """
    import numpy as np
    import torch
    from torch.utils.data import Dataset
    from transformers import (
        AutoModelForSequenceClassification, AutoTokenizer, DataCollatorWithPadding,
        Trainer, TrainingArguments,
    )

    name = "distilroberta-base"
    tok = AutoTokenizer.from_pretrained(name)
    idx = {c: i for i, c in enumerate(DISTRESS_CLASSES)}

    class DS(Dataset):
        def __init__(self, texts, labels):
            self.enc = tok(list(texts), truncation=True, max_length=max_len)
            self.labels = [idx[l] for l in labels]

        def __len__(self):
            return len(self.labels)

        def __getitem__(self, i):
            item = {k: v[i] for k, v in self.enc.items()}
            item["labels"] = self.labels[i]
            return item

    use_mps = torch.backends.mps.is_available()
    print(f"device: {'mps (Apple GPU)' if use_mps else 'cpu'} | max_len {max_len} | batch {batch}")

    model = AutoModelForSequenceClassification.from_pretrained(
        name, num_labels=len(DISTRESS_CLASSES)
    )
    args = TrainingArguments(
        output_dir=str(OUT / "ckpt"), num_train_epochs=epochs,
        per_device_train_batch_size=batch, per_device_eval_batch_size=batch * 2,
        learning_rate=2e-5, eval_strategy="epoch", save_strategy="no",
        logging_steps=100, report_to=[], use_cpu=not use_mps,
        dataloader_pin_memory=False,
        # Adafactor, not AdamW. AdamW keeps two fp32 moments per parameter --
        # ~650 MB of optimiser state for distilroberta, allocated regardless of
        # batch size, which is exactly what was OOMing (the traceback lands in
        # adamw.py, not in the forward pass). Adafactor factorises the second
        # moment and uses a fraction of that. Shrinking the batch does not help
        # with an optimiser-state OOM; changing the optimiser does.
        optim="adafactor",
        gradient_checkpointing=True,
    )
    trainer = Trainer(
        model=model, args=args,
        train_dataset=DS(X_tr, y_tr), eval_dataset=DS(X_te, y_te),
        data_collator=DataCollatorWithPadding(tok),
    )
    trainer.train()

    pred = np.argmax(trainer.predict(DS(X_te, y_te)).predictions, axis=1)
    pred_labels = [DISTRESS_CLASSES[i] for i in pred]

    OUT.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(OUT)
    tok.save_pretrained(OUT)

    return {
        "model": name,
        "device": "mps" if use_mps else "cpu",
        "max_len": max_len,
        "epochs": epochs,
        "n_train": len(X_tr),
        "n_test": len(X_te),
        "report": classification_report(
            y_te, pred_labels, labels=DISTRESS_CLASSES, output_dict=True, zero_division=0
        ),
        "confusion": confusion_matrix(y_te, pred_labels, labels=DISTRESS_CLASSES).tolist(),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", action="store_true", help="TF-IDF only, seconds not minutes")
    ap.add_argument("--no-supplement", action="store_true",
                    help="GoEmotions only -- the ablation showing what the gap classes cost")
    ap.add_argument("--epochs", type=int, default=2)
    ap.add_argument("--max-len", type=int, default=64)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--sample", type=int, default=0,
                    help="train on a stratified subsample this size "
                         "(0 = all). The TEST set is never subsampled.")
    a = ap.parse_args()

    texts, labels = load_distress_data(include_supplement=not a.no_supplement)
    print(json.dumps(report(labels), indent=2))

    X_tr, X_te, y_tr, y_te = train_test_split(
        texts, labels, test_size=0.15, random_state=42, stratify=labels
    )
    if a.sample and a.sample < len(X_tr):
        # stratified, so the rare classes survive -- overwhelm is only 1.8%
        X_tr, _, y_tr, _ = train_test_split(
            X_tr, y_tr, train_size=a.sample, random_state=42, stratify=y_tr
        )
        print(f"subsampled training set to {len(X_tr)} (stratified). "
              f"Report this alongside the metrics.")
    print(f"train {len(X_tr)}  test {len(X_te)}")

    res = run_baseline(X_tr, y_tr, X_te, y_te) if a.baseline \
        else run_transformer(X_tr, y_tr, X_te, y_te, a.epochs, a.max_len, a.batch)
    res["supplement"] = not a.no_supplement

    macro = res["report"]["macro avg"]["f1-score"]
    print(f"\n=== {res['model']}  macro-F1 = {macro:.3f} ===")
    for c in DISTRESS_CLASSES:
        r = res["report"].get(c, {})
        print(f"  {c:22s} P {r.get('precision',0):.2f}  R {r.get('recall',0):.2f} "
              f" F1 {r.get('f1-score',0):.2f}   n={int(r.get('support',0))}")

    OUT.mkdir(parents=True, exist_ok=True)
    tag = "baseline" if a.baseline else "transformer"
    tag += "_nosupp" if a.no_supplement else ""
    (OUT / f"metrics_{tag}.json").write_text(json.dumps(res, indent=2))
    print(f"\nwrote {OUT / f'metrics_{tag}.json'}  <- this is the midterm slide")


if __name__ == "__main__":
    main()
