# Cleanup Log

## 2026-03-04

- Created `REPO_INVENTORY.md` with full local audit summary.
- Created `CLEANUP_PLAN.md` before any move/delete operations.
- Created archive root: `archive/legacy_generated/pre_2026_03_04_rebuild/`.
- Archived prior non-authoritative status dossiers:
  - `reports/internal/eptesicu_labs_internal_status_report.md`
  - `reports/internal/eptesicu_labs_internal_status_report.pdf`
- Archived legacy generated reports and release artifacts:
  - `reports/train`, `reports/eval`, `reports/export`, `reports/cost`
  - `reports/release_decision.json`
  - `reports/release_decision_audit.json`
  - `reports/model_card_draft.md`
  - `reports/still_can_fail.md`
- Archived legacy outputs:
  - `outputs/train`, `outputs/checkpoints`, `outputs/exports`
- Archived legacy dataset output trees:
  - `Dataset/output`
  - `Dataset/identity_dataset/output/*` except `full_run_codex_spark_xhigh`
  - `Dataset/identity_dataset/identity_dataset/output`
- Archived superseded stack:
  - `pipelines`, `tests`, `manifests`, `Plan`, `.sisyphus`
- Archived legacy config/data/report remnants:
  - `configs/*`
  - `data/*`
  - `reports/data` (as `legacy_config_data/reports_data_legacy`)
  - `reports/internal` already archived by file move
- Archived scratch instead of deleting:
  - `.ruff_cache`
  - `Dataset/identity_dataset/tmp_worker_test.txt`
  - `Dataset/identity_dataset/_tmp_worker_test.py`
- Preserved canonical identity pack in-place:
  - `Dataset/identity_dataset/output/full_run_codex_spark_xhigh/*`
