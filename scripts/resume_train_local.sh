#!/usr/bin/env bash
set -euo pipefail

echo "Status: non-canonical convenience wrapper."
echo "Resume is notebook-driven, not script-driven."
echo
echo "Use these active files:"
echo "- configs/train_sft.yaml"
echo "- configs/train_dpo.yaml"
echo "- notebooks/40_train_sft_unsloth_qwen35_4b.ipynb"
echo "- notebooks/50_train_dpo_unsloth_qwen35_4b.ipynb"
echo
echo "Recommended resume flow:"
echo "1. Open notebook 40 for SFT resume and set the checkpoint path explicitly."
echo "2. Open notebook 50 for DPO resume and point it at the intended SFT artifact."
echo "3. Write proof-bearing outputs under workspace/runs/<run_id>/."
