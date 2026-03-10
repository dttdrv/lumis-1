#!/usr/bin/env bash
set -euo pipefail

echo "Status: non-canonical convenience wrapper."
echo "Resume is notebook-driven, not script-driven."
echo
echo "Use these active files:"
echo "- THE NOTEBOOK.ipynb"
echo "- configs/train_sft.yaml"
echo "- configs/train_dpo.yaml"
echo
echo "Recommended resume flow:"
echo "1. Open notebook 91 and select the intended resume point inside the single-notebook flow."
echo "2. Set the checkpoint or artifact path explicitly before resuming SFT, DPO, export, or eval."
echo "3. Write proof-bearing outputs under workspace/runs/<run_id>/."
