# NOTEBOOK_OPERATOR_INSTRUCTIONS

Status: Canonical | Descriptive

This file explains how to run the Lumis-1 notebook surfaces after the 2026-03-08 rehab pass.

## The Unified Notebook

The single sequential Colab notebook is:

- `notebooks/90_colab_main_pipeline.ipynb`
- `C:\\Users\\deyan\\Projects\\Lumis-1\\notebooks\\90_colab_main_pipeline.ipynb`

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

1. Mount Drive and create one working root under `/content/lumis1_main`
2. Install the pinned dependency baseline embedded inside the notebook
3. Materialize the notebook’s embedded runtime/config surface locally
4. Validate the identity dataset
5. Rewrite placeholder identity image references into concrete surrogate local image assets
6. Build the open corpus from allowlisted HF sources and materialize supported multimodal images into local rows carrying `image`, `path`, and `image_path`
7. Merge and validate the final dataset
8. Run SFT
9. Run DPO
10. If DPO fails, record that failure in run evidence and continue downstream from the SFT artifact
11. Export GGUF first
12. Run eval/export smoke against the effective final model
13. Copy artifacts to Drive and optionally download one GGUF file to the browser

## Identity Input

Notebook 90 uses this input folder:

- `/content/drive/MyDrive/lumis1_colab/identity_input`

If the folder already contains the identity files, the notebook uses them directly.

If the files are missing, notebook 90 now auto-downloads them from the default Hugging Face dataset repo:

- `STnoui/lumis1-identity`

The expected canonical filenames are:

- `sft_dataset.jsonl`
- `preference_dataset.jsonl`

The accepted aliases are still:

- `identity_sft.jsonl`
- `identity_preferences.jsonl`

You only need to override this behavior if:

- you want a different HF dataset repo, in which case set `LUMIS1_IDENTITY_HF_REPO`
- you want to disable auto-download and provide the files yourself

Notebook 90 now defaults `PROFILE` to `auto`, which resolves to a safer memory profile from the detected GPU rather than assuming a 96 GB class device.

Notebook 90 now installs pinned dependencies in place without intentionally killing the kernel. It also retries Colab Drive mounting safely when `/content/drive` is already present and non-empty in the runtime.

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

Notebook 90 is no longer text-only by design. It now tries to build a real multimodal SFT surface by:

- rewriting placeholder identity image references into surrogate local screenshot/document images
- materializing supported HF multimodal records into concrete local image rows with public-compatible `image`, `path`, and `image_path` keys
- switching to `FastVisionModel` SFT when multimodal rows are present

It also no longer treats DPO as a single point of failure. If the DPO stage fails, notebook 90 records that failure under the DPO run evidence tree and continues export/eval from the SFT artifact instead of aborting the whole Colab session.

The GGUF export stage also now retries direct Unsloth loads from both merged and adapter-backed model directories instead of giving up after the first generic merge failure.

That still does not make the path proof-bearing yet. Two important risks remain:

- identity multimodal rows are trained against surrogate images, not curated original screenshots/documents
- the HF multimodal source mapping is heuristic and still unproven on a real Colab run

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

If `workspace/runs/<run_id>/reports/export_smoke.json` reports `status = structural_only`, the notebook completed unattended and produced the required GGUF variants, but parity-pair verification was not available. Treat that as structurally usable, not as exact parity proof.

## If You Want The Modular Path Instead

Use `OPERATOR_RUN_ORDER.md` and run the canonical notebook sequence `00 -> 10 -> 20 -> 30 -> 40 -> 50 -> 60`.

