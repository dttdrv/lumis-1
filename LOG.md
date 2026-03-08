# LOG

## 2026-03-04

- Archived stale generated outputs and superseded notes to `archive/20260304_222305`.
- Added `archive/README.md` documenting moved files and rationale.
- Replaced all required configs with strict Lumis-1 policy-aligned versions.
- Added `INPUT_CONTRACT_IDENTITY.md` for required identity filenames and schema/count contract.
- Reworked `lumis1/` utility modules for schema validation, license attestation, ingestion, filters, CoT scrubbing, vision schema checks, mixing math, hashing, and export smoke checks.
- Reworked required tests: `test_schema.py`, `test_mixing_math.py`, `test_cot_scrub.py`.
- Regenerated required notebooks:
  - `notebooks/00_env_sanity_and_pinning.ipynb`
  - `notebooks/10_validate_identity_pack.ipynb`
  - `notebooks/20_build_open_dataset_mix.ipynb`
  - `notebooks/30_merge_and_validate_full_dataset.ipynb`
  - `notebooks/40_train_sft_unsloth_qwen35_4b.ipynb`
  - `notebooks/50_train_dpo_unsloth_qwen35_4b.ipynb`
  - `notebooks/60_eval_export_smoke.ipynb`
- Updated operator documentation and model card draft for strict manual RunPod execution flow.
- Added detailed summary report: `DETAILED_LOCAL_BUILD_REPORT.md`.

## 2026-03-06

- Added PM-facing repository audit report: `PM_REPOSITORY_AUDIT_2026-03-06.md`.
- Generated corrected full-tree inventory appendix under `workspace/reports/pm_audit_20260306_corrected/`.
- Re-ran unit tests: `16 passed`.
- Re-ran config YAML parsing and notebook JSON/code-cell validation successfully.
- Re-ran `scripts/audit_active_generation_paths.py`; active paths remained clean under the repo's heuristic audit.
- Ran a fresh CLI Trivy filesystem scan at HIGH/CRITICAL; all 63 findings were confined to archived legacy material, with 0 findings in active/current paths.
- Confirmed script/config drift in the active scaffold: `scripts/validate_identity_pack.py` and `scripts/validate_full_dataset.py` now fail against the current `configs/dataset_mixture.yaml` schema, and the script layer is no longer the most reliable execution path.

## 2026-03-08

- Created `PROJECT_CHANGELOG_DETAILED.md` and `PROJECT_TIME_CAPSULE.md` as mandatory in-repo memory.
- Declared the notebook/config/runtime path as canonical and the archive as historical-only.
- Added shared runtime helpers for identity validation, full-dataset validation, manifest generation, and run-evidence scaffolding.
- Repaired `scripts/validate_identity_pack.py`, `scripts/validate_full_dataset.py`, and `scripts/render_dataset_manifest.py` as thin parity wrappers.
- Retired `scripts/build_open_corpus.py` and `scripts/merge_full_warehouse.py` as explicit notebook-routing shims.
- Updated operator shell wrappers so they no longer imply a working legacy script pipeline.
- Updated notebooks 00, 10, 30, 50, and 60 to reflect the canonical path and run-evidence policy.
- Added `scripts/build_colab_main_notebook.py` and generated `notebooks/90_colab_main_pipeline.ipynb` as a sequential Colab convenience surface.
- Added regression coverage for the Colab main notebook and re-ran the full test suite: `36 passed`.
- Re-ran notebook JSON/code-cell validation across all active notebooks, including notebook 90.
- Hardened notebook 90 for Qwen3.5 non-thinking mode with explicit tokenizer chat-template probes using `enable_thinking=False`.
- Hardened notebook 90 install behavior so repo-pinned Colab runs resync constrained package versions instead of only checking missing imports.
- Added a default guard that refuses the unverified multimodal SFT path when image-text rows are present in the merged dataset.
- Updated `scripts/build_colab_main_notebook.py` so it no longer risks overwriting notebook 90 with an empty placeholder.
- Repaired DPO preference normalization drift so notebook 50 and notebook 90 accept merged preference rows with either `prompt` or `prompt_messages`.
- Updated notebook 30 and notebook 90 merge logic so identity preference rows are rewritten into the canonical current shape before `full_preferences.jsonl` is written.
- Aligned Colab bootstrap contracts with the repo surface: notebook 90 and the helper script now accept documented identity-file aliases, default to an env-selectable stable branch instead of a hardcoded feature branch, and use the dedicated `*-export` run for GGUF artifacts.
- Expanded regression coverage for the Colab notebook and main pipeline contracts; the full test suite now passes with `41 passed`.
- Added `NOTEBOOK_OPERATOR_INSTRUCTIONS.md` documenting where the unified Colab notebook lives, how it relates to the canonical modular notebook path, and how to run the notebook surfaces without overstating what is proven.
