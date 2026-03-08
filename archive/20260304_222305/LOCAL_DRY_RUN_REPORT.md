# Local Dry-Run Report

Date: 2026-03-04 (Europe/Sofia)
Scope: local-only verification without remote training execution

## What was tested locally

1. Python syntax compile
- Command: `python -m compileall scripts`
- Result: pass

2. Canonical identity pack validation
- Command: `python scripts/validate_identity_pack.py --config configs/dataset_mixture.yaml --strict`
- Result: pass
- Verified counts:
  - SFT: 100000
  - Preferences: 25000
  - Multimodal: 9515
  - Text-only: 90485

3. Open corpus build (synthetic dry-run)
- Command: `python scripts/build_open_corpus.py --config configs/dataset_mixture.yaml --source-mode synthetic --dry-run --small-sample`
- Result: pass
- Output rows:
  - Open SFT: 5000
  - Open preferences: 5000

4. Merge full warehouse (dry-run)
- Command: `python scripts/merge_full_warehouse.py --config configs/dataset_mixture.yaml --open-sft workspace/interim/open_sft.jsonl --open-preferences workspace/interim/open_preferences.jsonl --dry-run --small-sample`
- Result: pass
- Output rows:
  - Full SFT: 6250
  - Full preferences: 2181

5. Full dataset validation (strict)
- Command: `python scripts/validate_full_dataset.py --config configs/dataset_mixture.yaml --full-sft workspace/final/full_sft.jsonl --full-preferences workspace/final/full_preferences.jsonl --strict`
- Result: pass
- Key checks:
  - identity share: 0.20
  - overall multimodal share: 0.12
  - non-identity multimodal share: 0.126 (target ~0.1262125)

6. Manifest rendering
- Command: `python scripts/render_dataset_manifest.py --config configs/dataset_mixture.yaml --full-sft workspace/final/full_sft.jsonl --full-preferences workspace/final/full_preferences.jsonl --validation-report workspace/reports/full_dataset_validation.json`
- Result: pass

7. Notebook JSON and parameter-cell structure
- Validation script run over all `notebooks/*.ipynb`
- Result: pass for 7/7 notebooks

8. Config YAML load checks
- Verified load for:
  - `configs/dataset_mixture.yaml`
  - `configs/train_sft_qwen35_4b_unsloth.yaml`
  - `configs/train_dpo_qwen35_4b_unsloth.yaml`
  - `configs/eval_gates.yaml`
- Result: pass

9. Security scan (local trivy)
- Command: `trivy fs --scanners misconfig,secret --severity HIGH,CRITICAL --skip-dirs archive --skip-dirs Dataset --format json --output workspace/reports/trivy_scan_workspace.json .`
- Result: pass
- Findings:
  - HIGH/CRITICAL misconfigurations: 0
  - HIGH/CRITICAL secrets: 0

## What was not tested locally

- Real HF ingestion mode (`--source-mode hf`) across all configured datasets.
- Actual Unsloth SFT/DPO training execution on GPU.
- Checkpoint resume behavior under long-running training interruptions.
- Vision fine-tuning throughput and memory behavior on target RunPod GPUs.
- Export quality parity pre/post GGUF or merged exports from a newly trained checkpoint.

## Environment gap observed

Current local environment is missing multiple training dependencies (`unsloth`, `unsloth_zoo`, `trl`, `datasets`, `accelerate`, `peft`, `bitsandbytes`, `jsonschema`), so full notebook execution is expected on prepared RunPod runtime instead of this local machine.
