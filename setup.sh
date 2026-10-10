#!/usr/bin/env bash
# Get a working ZenAI training environment. Run once, from the repo root.
#
#   ./setup.sh
#
# Works on macOS with the system Python 3.9. Docker is not required.
set -euo pipefail

echo "==> virtualenv"
python3 -m venv .venv
.venv/bin/pip install --quiet --upgrade pip

echo "==> dependencies"
# numpy<2 is not optional -- see the comment in pyproject.toml
.venv/bin/pip install --quiet \
  "scikit-learn" "pandas" "pyarrow" "numpy<2" \
  "torch" "transformers" "accelerate>=0.26" \
  "fastapi" "uvicorn" "pydantic-settings" "httpx" "sqlalchemy" "redis" "joblib" \
  "eval_type_backport" \
  "python-pptx" "python-docx" "pillow" "pytest" "ruff"
# eval_type_backport: Pydantic on Python 3.9 cannot evaluate `int | None` in a
# model without it, and /analyze dies on import. Pydantic's own documented fix.

echo "==> data (once, ~30MB)"
mkdir -p data/raw && cd data/raw
BASE=https://huggingface.co/datasets/google-research-datasets/go_emotions/resolve/main/simplified
for s in train validation test; do
  [ -f "$s-00000-of-00001.parquet" ] || curl -sLO "$BASE/$s-00000-of-00001.parquet"
done
if [ ! -d empatheticdialogues ]; then
  curl -sLO https://dl.fbaipublicfiles.com/parlai/empatheticdialogues/empatheticdialogues.tar.gz
  tar xzf empatheticdialogues.tar.gz
fi
[ -f ESConv.json ] || curl -sL -o ESConv.json https://huggingface.co/datasets/thu-coai/esconv/resolve/main/ESConv.json
cd ../..

echo "==> train the baseline distress model (seconds) so /analyze has something to serve"
.venv/bin/python -m training.train_distress --baseline > /dev/null && echo "    models/distress/tfidf.joblib"
.venv/bin/python -m training.train_drift > /dev/null && echo "    models/fidelity/drift.joblib"

echo
echo "Ready. Now:"
echo "  .venv/bin/python -m training.datasets                      # class balance"
echo "  .venv/bin/python -m training.train_distress --baseline     # seconds"
echo "  .venv/bin/python -m training.train_distress --cpu --sample 12000   # transformer, ~1h"
echo "  .venv/bin/uvicorn zenai.api.main:app --app-dir src            # then open /docs"
