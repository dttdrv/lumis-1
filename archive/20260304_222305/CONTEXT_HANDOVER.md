# Lumis-1 Detailed Context Handover

Last updated: 2026-03-04 (local workspace)
Repository root: `C:\Users\deyan\Projects\Lumis-1`

## 1. Mission and Non-Negotiables

This workspace was rebuilt as a **local-only, reproducible** build stack for Lumis-1.

Hard constraints applied:

- No claims of remote access or remote execution.
- No claims that training already ran.
- Canonical identity pack is fixed 20% slice; not regenerated.
- Thinking targets are disabled; vision support remains enabled.
- Dataset pipeline enforces lawful/allowlist behavior with explicit review-required sources.

## 2. Canonical Identity Pack Status

Canonical directory (preserved):

- `Dataset/identity_dataset/output/full_run_codex_spark_xhigh`

Verified local contract:

- `sft_dataset.jsonl`: 100000 rows
- `preference_dataset.jsonl`: 25000 rows
- `multimodal_manifest.json`: 9515 multimodal, 90485 text-only
- `run_manifest.json`: status `completed`

Validation report:

- `workspace/reports/identity_validation.json`

## 3. Cleanup and Archival Actions

All superseded generated artifacts were moved (not destroyed) under:

- `archive/legacy_generated/pre_2026_03_04_rebuild/`

Includes:

- Prior generated status dossiers and release/eval/train artifacts
- Legacy pipeline/test/manifests/plans stack
- Legacy data/config trees and stale run outputs

Non-authoritative warning marker:

- `archive/legacy_generated/pre_2026_03_04_rebuild/NON_AUTHORITATIVE_NOTE.md`

Audit trail files:

- `REPO_INVENTORY.md`
- `CLEANUP_PLAN.md`
- `CLEANUP_LOG.md`

## 4. Created Deliverables

### Docs and governance

- `README_CURRENT_STATE.md`
- `SOURCE_REGISTRY.md`
- `source_registry.yaml`
- `DATASET_ALLOWLIST_AND_LICENSE_NOTES.md`
- `REQUIRED_INPUTS.md`
- `MANUAL_RUNPOD_HANDOFF.md`
- `WHAT_STILL_CAN_FAIL.md`
- `LOCAL_DRY_RUN_REPORT.md`
- `FINAL_SUMMARY.md`
- `PROJECT_BRIEF.md`
- `STATE.yaml`
- `LOG.md`

### Configs

- `configs/dataset_mixture.yaml`
- `configs/train_sft_qwen35_4b_unsloth.yaml`
- `configs/train_dpo_qwen35_4b_unsloth.yaml`
- `configs/eval_gates.yaml`
- `.env.example`
- `requirements.txt`
- `constraints.txt`

### Scripts

- `scripts/common_dataset.py`
- `scripts/validate_identity_pack.py`
- `scripts/build_open_corpus.py`
- `scripts/merge_full_warehouse.py`
- `scripts/validate_full_dataset.py`
- `scripts/render_dataset_manifest.py`
- `scripts/launch_train_local.sh`
- `scripts/resume_train_local.sh`
- `scripts/export_artifacts.sh`

### Notebooks

- `notebooks/00_repo_audit_and_cleanup.ipynb`
- `notebooks/10_validate_identity_pack.ipynb`
- `notebooks/20_build_open_dataset_mix.ipynb`
- `notebooks/30_merge_and_validate_full_dataset.ipynb`
- `notebooks/40_train_sft_unsloth_qwen35_4b.ipynb`
- `notebooks/50_train_dpo_unsloth_qwen35_4b.ipynb`
- `notebooks/60_eval_export_smoke.ipynb`

## 5. Dataset Math and Policy Implementation

Target full mix implemented in config:

- General polished: 30%
- Real user: 20%
- Multilingual: 15%
- Utility: 15%
- Identity: 20%

Modality overlay targets:

- Text-only: 88%
- Image-text: 12%

Derived implemented requirement:

- Non-identity 80% multimodal target set to `0.1262125` (~12.6%)

Pipeline behavior:

- Normalization to canonical `messages` schema
- Role/content normalization (text and multimodal blocks)
- Thinking-leak marker filtering
- Fake tool/memory claim filtering
- Dedupe and near-duplicate checks
- Language histogram reporting
- Per-source before/after counts + drop counters
- Mixture and modality reconciliation

## 6. Primary Sources Captured

Registered in `SOURCE_REGISTRY.md` and `source_registry.yaml`, including:

- Unsloth Qwen3.5 fine-tuning and vision docs
- Unsloth datasets and RL guides
- Hugging Face Qwen model cards
- Target dataset cards
- Tulu-3 methodology reference

## 7. Local Verification Evidence

Executed and passed:

1. `python -m compileall scripts`
2. `python scripts/validate_identity_pack.py --config configs/dataset_mixture.yaml --strict`
3. `python scripts/build_open_corpus.py --config configs/dataset_mixture.yaml --source-mode synthetic --dry-run --small-sample`
4. `python scripts/merge_full_warehouse.py --config configs/dataset_mixture.yaml --open-sft workspace/interim/open_sft.jsonl --open-preferences workspace/interim/open_preferences.jsonl --dry-run --small-sample`
5. `python scripts/validate_full_dataset.py --config configs/dataset_mixture.yaml --full-sft workspace/final/full_sft.jsonl --full-preferences workspace/final/full_preferences.jsonl --strict`
6. `python scripts/render_dataset_manifest.py --config configs/dataset_mixture.yaml --full-sft workspace/final/full_sft.jsonl --full-preferences workspace/final/full_preferences.jsonl --validation-report workspace/reports/full_dataset_validation.json`
7. Notebook JSON/parameter-cell validation for all 7 notebooks
8. Trivy scan (workspace paths) with HIGH/CRITICAL secrets/misconfigs: 0 findings

Generated dry-run artifacts:

- `workspace/interim/open_sft.jsonl`
- `workspace/interim/open_preferences.jsonl`
- `workspace/final/full_sft.jsonl`
- `workspace/final/full_preferences.jsonl`
- `workspace/final/dataset_manifest.json`
- `workspace/reports/*.json` (validation + merge + trivy + build reports)

## 8. Known Gaps and Untested Until RunPod

- Full real ingestion with `--source-mode hf` across all configured datasets.
- Full GPU SFT/DPO execution and checkpoint resume.
- Post-train eval quality gates on actual trained checkpoints.
- Export parity checks on real trained weights.
- Legal resolution for review-required data sources (non-commercial or mixed-license subsets).

Environment caveat identified locally:

- Local machine is missing several training packages (`unsloth`, `trl`, `datasets`, etc.), so end-to-end training must be performed on prepared runtime (e.g., RunPod).

## 9. Next Operator Execution Order

1. `notebooks/10_validate_identity_pack.ipynb`
2. `notebooks/20_build_open_dataset_mix.ipynb` (`SOURCE_MODE='synthetic'` first, then `'hf'`)
3. `notebooks/30_merge_and_validate_full_dataset.ipynb`
4. Upload artifacts to RunPod manually
5. `notebooks/40_train_sft_unsloth_qwen35_4b.ipynb`
6. `notebooks/50_train_dpo_unsloth_qwen35_4b.ipynb` (optional after SFT)
7. `notebooks/60_eval_export_smoke.ipynb`

## 10. Fast Resume Checklist for Next Session

- Confirm canonical identity pack path still intact.
- Re-run identity validation script first.
- Decide legal allow/deny for `review_required` sources before `source_mode=hf` full ingest.
- Confirm runtime dependency install against `requirements.txt` + `constraints.txt`.
- Keep notebook config cells as single source of run parameters.
- Preserve run manifests in output folders for reproducibility.
