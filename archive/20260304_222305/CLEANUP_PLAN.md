# Cleanup Plan (Pre-Execution)

Plan timestamp: 2026-03-04 (Europe/Sofia)
Rule: No deletions before plan entry. Prefer archival under `archive/legacy_generated/`.

## Objectives

- Preserve canonical identity inputs and user-relevant artifacts.
- Remove ambiguity from stale generated status/training artifacts.
- Create a clean workspace for local dataset build + Unsloth notebooks.

## Planned actions

1. Create archive root
- Action: create `archive/legacy_generated/pre_2026_03_04_rebuild/`
- Reason: centralize superseded generated artifacts without data loss.
- Status: completed

2. Archive prior non-authoritative status dossiers
- Move:
  - `reports/internal/eptesicu_labs_internal_status_report.md`
  - `reports/internal/eptesicu_labs_internal_status_report.pdf`
- Reason: these can be mistaken for actual execution evidence; keep only as archived historical artifacts.
- Status: completed

3. Archive legacy generated training/eval/output artifacts
- Move directories:
  - `reports/train`
  - `reports/eval`
  - `reports/export`
  - `reports/cost`
  - `outputs/train`
  - `outputs/checkpoints`
  - `outputs/exports`
- Move files:
  - `reports/release_decision.json`
  - `reports/release_decision_audit.json`
  - `reports/model_card_draft.md`
  - `reports/still_can_fail.md`
- Reason: stale generated artifacts from previous flow that can confuse operator.
- Status: completed

4. Archive bulky legacy dataset outputs (non-canonical)
- Move directories:
  - `Dataset/output`
  - `Dataset/identity_dataset/output/*` except `full_run_codex_spark_xhigh`
  - `Dataset/identity_dataset/identity_dataset/output`
- Reason: keep canonical identity pack visible while preserving old runs.
- Status: completed

5. Archive superseded implementation stack
- Move directories:
  - `pipelines`
  - `tests`
  - `manifests`
  - `Plan`
  - `.sisyphus`
- Reason: superseded by new reproducible scripts/notebooks/configs for this mission.
- Status: completed

6. Archive legacy configs/data and residual report folders
- Move directories:
  - `configs/*` (legacy config trees from prior flow)
  - `data/*` (legacy prepared/intermediate artifacts)
  - `reports/data`
  - `reports/internal`
- Reason: avoid mixing old pipeline state with new reproducible build stack.
- Status: completed

7. Remove disposable caches/scratch
- Delete:
  - `.ruff_cache`
  - `**/__pycache__` directories where present
  - `Dataset/identity_dataset/tmp_worker_test.txt`
  - `Dataset/identity_dataset/_tmp_worker_test.py`
- Reason: non-authoritative scratch/cache.
- Status: completed_with_archive_substitution

8. Preserve canonical identity pack and identity source
- Keep untouched:
  - `Dataset/identity_dataset/output/full_run_codex_spark_xhigh/*`
  - `Dataset/identity_dataset/*.py` and related identity source docs/configs
- Reason: required canonical 20% identity slice input.
- Status: completed

## Post-cleanup acceptance checks

- Canonical identity pack still present and line counts unchanged.
- New root structure contains only active configs/scripts/notebooks/docs + preserved canonical inputs.
- All archived prior execution claims are clearly non-authoritative historical artifacts.
