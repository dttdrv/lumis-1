# NOTEBOOK_OPERATOR_INSTRUCTIONS

Status: Canonical | Descriptive

This file explains how to run the Lumis-1 notebook surfaces after the 2026-03-08 rehab pass.

## The Unified Notebook

The single sequential Colab notebook is:

- `notebooks/90_colab_main_pipeline.ipynb`\r\n- `C:\\Users\\deyan\\Projects\\Lumis-1\\notebooks\\90_colab_main_pipeline.ipynb`

It is a convenience wrapper for operators who cannot run the modular notebooks side by side.

It does not replace repository truth. The underlying canonical stages are still:

1. `notebooks/00_env_sanity_and_pinning.ipynb`
2. `notebooks/10_validate_identity_pack.ipynb`
3. `notebooks/20_build_open_dataset_mix.ipynb`
4. `notebooks/30_merge_and_validate_full_dataset.ipynb`
5. `notebooks/40_train_sft_unsloth_qwen35_4b.ipynb`
6. `notebooks/50_train_dpo_unsloth_qwen35_4b.ipynb`
7. `notebooks/60_eval_export_smoke.ipynb`

## What Notebook 90 Actually Does

`90_colab_main_pipeline.ipynb` is intended to run the current active path in one Colab session:

1. Mount Drive and clone `dttdrv/lumis-1`
2. Install the repo-pinned dependency baseline
3. Validate the identity dataset
4. Build the open corpus
5. Merge and validate the final dataset
6. Run SFT
7. Run DPO
8. Export GGUF first
9. Run eval/export smoke
10. Copy artifacts to Drive and optionally download one GGUF file to the browser

## What You Must Provide

Notebook 90 expects an identity input folder containing either the preferred canonical names:

- `sft_dataset.jsonl`
- `preference_dataset.jsonl`

or the accepted aliases:

- `identity_sft.jsonl`
- `identity_preferences.jsonl`

The default Colab location is:

- `/content/drive/MyDrive/lumis1_colab/identity_input`

## What Is Proven vs Unproven

Proven:

- The notebook exists on `main`.
- The notebook compiles.
- The repo test suite passed after the current rehab work.
- The canonical identity dataset remains the strongest completed artifact.

Unproven:

- A real proof-bearing end-to-end Colab run using notebook 90.
- Production-scale open/full dataset assembly from notebook 90.
- Completed SFT, DPO, eval, or GGUF export until `workspace/runs/<run_id>/` contains real evidence.
- A proof-bearing multimodal Qwen3.5 SFT path for the current mixed dataset.

## Important Current Limitation

Notebook 90 is not yet a guaranteed end-to-end multimodal trainer.

The current repo still lacks a proof-bearing FastVisionModel-based SFT path for the image-text rows present in the active dataset mix. The notebook is intentionally conservative around that gap.

## Expected Evidence

Treat training, DPO, evaluation, and export as real only when the notebook writes evidence under:

- `workspace/runs/<run_id>/STATUS.json`
- `workspace/runs/<run_id>/SUMMARY.md`
- `workspace/runs/<run_id>/config_snapshot/`
- `workspace/runs/<run_id>/commands/`
- `workspace/runs/<run_id>/environment/`
- `workspace/runs/<run_id>/logs/`
- `workspace/runs/<run_id>/reports/`
- `workspace/runs/<run_id>/artifacts/`
- `workspace/runs/<run_id>/checksums/`

If those directories are not populated, do not treat the run as complete.

## If You Want The Modular Path Instead

Use `OPERATOR_RUN_ORDER.md` and run the canonical notebook sequence `00 -> 10 -> 20 -> 30 -> 40 -> 50 -> 60`.

