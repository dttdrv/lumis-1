# Archive Log

## 2026-03-04 22:23:05 +02:00

Archive folder: `archive/20260304_222305`

Moved stale generated artifacts from prior local build iteration to keep the active workspace aligned with the Lumis-1 local-only rebuild requirements.

Moved items:
- `00_repo_audit_and_cleanup.ipynb`
- `CLEANUP_LOG.md`
- `CLEANUP_PLAN.md`
- `CONTEXT_HANDOVER.md`
- `DATASET_ALLOWLIST_AND_LICENSE_NOTES.md`
- `eval_gates.yaml`
- `FINAL_SUMMARY.md`
- `LOCAL_DRY_RUN_REPORT.md`
- `MANUAL_RUNPOD_HANDOFF.md`
- `outputs/`
- `README_CURRENT_STATE.md`
- `reports/`
- `REPO_INVENTORY.md`
- `REQUIRED_INPUTS.md`
- `RUNPOD_NEXT_STEPS_DETAILED_REPORT.md`
- `SOURCE_REGISTRY.md`
- `train_dpo_qwen35_4b_unsloth.yaml`
- `train_sft_qwen35_4b_unsloth.yaml`
- `WHAT_STILL_CAN_FAIL.md`

Reason:
- These files were generated outputs, handoff notes, or superseded configs from the previous build cycle.
- They are preserved for auditability but excluded from the active path for the new constrained rebuild.

Safety notes:
- No user-provided PDF files were moved.
- No files under `Dataset/identity_dataset/` were modified or moved.
