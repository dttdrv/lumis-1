#!/usr/bin/env bash
set -euo pipefail

FULL_SFT="${1:-workspace/final/full_sft.jsonl}"
FULL_PREF="${2:-workspace/final/full_preferences.jsonl}"

echo "Status: canonical checker/helper only."
echo "Export execution remains notebook-driven in notebooks/60_eval_export_smoke.ipynb."
echo "This script only verifies prepared dataset artifacts and refreshes the canonical dataset manifest."

[[ -f "$FULL_SFT" ]] || { echo "Missing $FULL_SFT"; exit 1; }
[[ -f "$FULL_PREF" ]] || { echo "Missing $FULL_PREF"; exit 1; }

python scripts/render_dataset_manifest.py \
  --full-sft "$FULL_SFT" \
  --full-preferences "$FULL_PREF" \
  --allow-small-sample

echo "Manifest refreshed. Use notebook 60 for any real eval/export execution and write evidence under workspace/runs/<run_id>/."
