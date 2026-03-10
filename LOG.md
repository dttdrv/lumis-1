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
- Hardened the single Colab notebook for one-pass execution: removed the forced install-time kernel kill, switched the default profile selection to GPU-memory-aware `auto`, and added placeholder-image text fallback for SFT.
- Repaired unified-notebook stage handoff for adapter outputs: DPO, eval, and GGUF export now detect PEFT adapter directories and handle them explicitly instead of assuming merged full-model checkpoints.
- Repaired the notebook builder so it reads notebook 90 with BOM-tolerant decoding and can normalize the canonical notebook again without crashing.
- Added unattended eval/export policy coverage: text-only training surfaces can report `multimodal_correctness = not_applicable`, and GGUF export can report `structural_only` when variants exist but parity-pair side inputs are absent.
- Added regression coverage for profile auto-resolution, model artifact layout detection, message normalization for chat-template rendering, and unattended eval/export status assessment; the full suite now passes with `43 passed`.
- Re-implemented notebook 90 as a standalone Colab surface that embeds its own runtime/config code and no longer depends on repo-side YAML/module files at execution time.
- Added `lumis1/colab_standalone.py` and `tests/test_colab_standalone.py` as the tested helper surface embedded into notebook 90.
- Rebuilt notebook 90 so it materializes surrogate local image assets for placeholder identity rows, builds concrete `image_path` rows for supported HF multimodal sources, attempts `FastVisionModel` SFT when multimodal rows exist, and carries the same run through DPO, GGUF export, eval, and Drive copy-out.
- Updated notebook 90 eval/export status handling so multimodal checks and structural GGUF export can complete coherently inside the standalone path.
- Re-ran the full test suite after the standalone notebook rebuild: `47 passed`.
- Re-ran notebook JSON/code-cell validation across all active notebooks after the rebuild.
- Embedded the actual `requirements.txt` plus `constraints.txt` install contract into notebook 90 instead of only embedding the constraint pins.
- Added explicit multimodal processor persistence through SFT, DPO, export, and eval, and made the export path prefer Unsloth-native merged saves before falling back to generic PEFT merge behavior.
- Rebuilt notebook 90 and re-ran the full suite after the Colab dependency/export hardening pass: `47 passed`.
- Hardened the standalone Colab notebook against multimodal handoff failures: DPO now fails closed into run evidence without aborting export/eval, GGUF export now retries direct Unsloth loads from both merged and adapter directories, and eval now follows the effective final model instead of assuming DPO completed.
- Repaired the standalone multimodal row format so notebook 90 now emits public-compatible `image`, `path`, and `image_path` keys instead of relying on a repo-local image field convention alone.
- Repaired the unified notebook handoff so DPO failure no longer aborts the full Colab run; export and eval now fall back to the SFT artifact while recording the DPO failure in run evidence.
- Rebuilt notebook 90 from the generator again after the hostile review pass and re-ran the full suite: `47 passed`.
- Repaired notebook 90 bootstrap so it now recovers Colab Drive mounting when `/content/drive` is already non-empty and auto-downloads missing identity files from `STnoui/lumis1-identity` before validation.
- Added `lumis1/colab_unified_unsloth_first.py`, `scripts/build_colab_unified_unsloth_first_notebook.py`, and generated `notebooks/91_colab_unified_unsloth_first.ipynb` as the new canonical Colab surface.
- Switched the default Colab contract from repo-pinned-first to Unsloth-first and added regression coverage for the new notebook 91 bootstrap/download/runtime guarantees.
- Added `colab_g4_first_run` to `configs/run_profiles.yaml` for a conservative first serious Colab G4 path.
- Updated project state and operator docs so notebook 91 is canonical and notebook 90 is legacy context only.

## 2026-03-09

- Generated `notebooks/91_colab_unified_unsloth_first.ipynb` from `scripts/build_colab_unified_unsloth_first_notebook.py` as the new canonical Colab surface.
- Added `lumis1/colab_unified_unsloth_first.py` as the embedded runtime helper for notebook 91.
- Switched the default Colab install contract to Unsloth-first and added a conservative `colab_g4_first_run` profile.
- Added notebook-91 regression coverage for the Unsloth-first contract, HF identity bootstrap, safe Drive recovery, automatic final download, and self-contained runtime embedding.
- Updated project/operator state so notebook 91 is canonical and notebook 90 is retained as legacy context.
- Renamed the older root notebook-91 snapshot to `notebooks/91_colab_unified_unsloth_first_old.ipynb` and promoted the newer notebook-91 variant from `workspace/trivy_scope_notebook91/` to the canonical root path after the hang investigation.

## 2026-03-10

- Simplified the active notebook tree to notebook 91 only and removed the modular notebook surfaces, notebook 90, and the old notebook-91 snapshot from `notebooks/`.
- Removed retired notebook-90 support and wrapper tests from the active tree, while leaving historical archive material and long-form historical reports untouched.
- Updated current operator docs, helper scripts, `PROJECT_BRIEF.md`, and `STATE.yaml` so the active execution model now points only to `notebooks/91_colab_unified_unsloth_first.ipynb`.
- Renamed the active notebook surface to `THE NOTEBOOK.ipynb`, moved it to the repository root, and archived the duplicate `workspace/trivy_scope_notebook91/` snapshot to leave only one live notebook-91 surface in the active tree.
