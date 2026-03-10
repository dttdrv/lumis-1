#!/usr/bin/env bash
set -euo pipefail

echo "Status: Canonical operator helper only."
echo "This script does not run the retired script-based dataset pipeline."
echo "It verifies the current prepared artifacts, refreshes the canonical manifest, and points you to notebook 91."

python scripts/validate_identity_pack.py --strict
python scripts/validate_full_dataset.py --allow-small-sample --strict
python scripts/render_dataset_manifest.py --allow-small-sample

echo
echo "Canonical notebook:"
echo "1. notebooks/91_colab_unified_unsloth_first.ipynb"
