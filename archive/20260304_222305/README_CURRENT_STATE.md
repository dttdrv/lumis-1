# Lumis-1 Local Build Workspace (Current State)

This repository is now organized for a **local-only, reproducible build flow** for Lumis-1 dataset preparation and Unsloth notebook training handoff.

## What this workspace now represents

- Local dataset planning/build tooling for:
  - canonical identity pack validation,
  - open-corpus assembly,
  - full-warehouse merge,
  - dataset validation and manifest rendering.
- Notebook stack for staged SFT and DPO on `Qwen/Qwen3.5-4B-Base` with Unsloth.
- Local smoke/eval/export utility notebook.
- Manual RunPod handoff instructions for a human operator.

## What this workspace does NOT claim

- No claim that training already ran.
- No claim of RunPod or remote machine access.
- No claim that stage metrics, cost, exports, or eval gates already passed.

## Canonical identity pack status

Canonical pack detected locally at:

- `Dataset/identity_dataset/output/full_run_codex_spark_xhigh/`

Validated local targets in that pack:

- SFT rows: `100000`
- Preference rows: `25000`
- Multimodal rows: `9515`
- Text-only rows: `90485`

This pack is treated as the fixed 20% identity slice in the full warehouse plan.

## Cleanup status

- Previous generated training/eval/release artifacts were archived under:
  - `archive/legacy_generated/pre_2026_03_04_rebuild/`
- Prior internal status dossiers were archived and are treated as historical/non-authoritative for this build.

See:

- `REPO_INVENTORY.md`
- `CLEANUP_PLAN.md`
- `CLEANUP_LOG.md`

## Build entry points

- Scripts: `scripts/`
- Notebooks: `notebooks/`
- Configs: `configs/`
- Operator instructions: `MANUAL_RUNPOD_HANDOFF.md`
