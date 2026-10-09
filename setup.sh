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
  "python-pptx" "python-docx" "pillow"

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
cd ../..

echo
echo "Ready. Now:"
echo "  .venv/bin/python -m training.datasets                      # class balance"
echo "  .venv/bin/python -m training.train_distress --baseline     # seconds"
echo "  .venv/bin/python -m training.train_distress                # ~20 min, CPU"
