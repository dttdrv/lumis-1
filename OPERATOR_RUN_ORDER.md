# OPERATOR_RUN_ORDER

Status: Canonical | Descriptive

This file defines the current notebook-first execution order only. It is not proof that the run was completed. Proof-bearing SFT, DPO, evaluation, or export claims require evidence under `workspace/runs/<run_id>/`.

## Mandatory Order

1. `00_env_sanity_and_pinning.ipynb`
2. `10_validate_identity_pack.ipynb`
3. `20_build_open_dataset_mix.ipynb`
4. `30_merge_and_validate_full_dataset.ipynb`
5. `40_train_sft_unsloth_qwen35_4b.ipynb`
6. `50_train_dpo_unsloth_qwen35_4b.ipynb`
7. `60_eval_export_smoke.ipynb`

## Sequential Colab Alternative

- `90_colab_main_pipeline.ipynb` is the single-notebook Colab orchestration surface.
- It is a convenience wrapper for operators who cannot run the modular notebooks side by side.
- It does not change repository truth: the underlying canonical stages are still `00 -> 10 -> 20 -> 30 -> 40 -> 50 -> 60`.
- It defaults to the repo-pinned dependency baseline and only uses the Unsloth auto-installer as a fallback.
- It expects the operator to point `IDENTITY_INPUT_DIR` at a folder containing `sft_dataset.jsonl` and `preference_dataset.jsonl`.
- It writes proof-bearing SFT, DPO, export, and eval artifacts under `workspace/runs/<run_id>/`.

## Success Artifacts By Step

### 00

- `workspace/reports/env_sanity.json`
- `workspace/reports/env_freeze.txt`

### 10

- `workspace/reports/identity_validation.json`

### 20

- `workspace/interim/open_sft.jsonl`
- `workspace/interim/open_preferences.jsonl`
- `workspace/reports/open_corpus_build_report.json`

### 30

- `workspace/final/full_sft.jsonl`
- `workspace/final/full_preferences.jsonl`
- `workspace/final/dataset_manifest.json`
- `workspace/reports/full_dataset_validation.json`
- `workspace/reports/mixture_math.json`

### 40

- `workspace/reports/train_sft_config_resolved.json`
- `workspace/runs/<run_id>/` evidence (if training executed)

### 50

- `workspace/reports/train_dpo_config_resolved.json`
- `workspace/runs/<run_id>/` evidence (if DPO executed)

### 60

- `workspace/reports/export_smoke.json`
- `workspace/runs/<run_id>/` evidence (if eval/export executed)
- GGUF exports containing at least one `q8_0` and one `q4*` file if export is executed

## Hard Validation Rules

- Identity pack is fixed 20% of final SFT mixture.
- Final CoT marker count must be `0`.
- Row- and token-weighted category and modality targets must pass tolerance checks.
- No unallowlisted dataset may be ingested.
- PRIVATE_LOCAL entries remain disabled unless all attestation fields are provided and valid.
