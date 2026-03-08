#!/usr/bin/env bash
set -euo pipefail

echo "Status: Canonical operator helper only."
echo "This script does not run the retired script-based dataset pipeline."
echo "It verifies the current prepared artifacts, refreshes the canonical manifest, and points you to the notebook-first path."

python scripts/validate_identity_pack.py --strict
python scripts/validate_full_dataset.py --allow-small-sample --strict
python scripts/render_dataset_manifest.py --allow-small-sample

echo
echo "Canonical notebook order:"
echo "1. notebooks/00_env_sanity_and_pinning.ipynb"
echo "2. notebooks/10_validate_identity_pack.ipynb"
echo "3. notebooks/20_build_open_dataset_mix.ipynb"
echo "4. notebooks/30_merge_and_validate_full_dataset.ipynb"
echo "5. notebooks/40_train_sft_unsloth_qwen35_4b.ipynb"
echo "6. notebooks/50_train_dpo_unsloth_qwen35_4b.ipynb"
echo "7. notebooks/60_eval_export_smoke.ipynb"
