# Repository Inventory (Local Audit)

Audit timestamp (Europe/Sofia): 2026-03-04T01:16:08+02:00
Audit scope: `C:\Users\deyan\Projects\Lumis-1`

## Top-level directories

- `.ruff_cache` (cache)
- `.sisyphus` (previous planning/evidence metadata)
- `configs` (legacy configs from prior pipeline)
- `data` (small prepared/normalized artifacts)
- `Dataset` (largest directory; identity + many generated outputs)
- `manifests` (legacy manifests)
- `outputs` (legacy checkpoint/export stubs)
- `pipelines` (legacy scripts)
- `Plan` (legacy plan markdown)
- `reports` (legacy reports and status dossiers)
- `tests` (legacy test suite for previous pipeline)

## Size and density snapshot

- `Dataset`: 3395 files, ~951.69 MB
- `pipelines`: 66 files, ~1.06 MB
- `tests`: 92 files, ~0.30 MB
- `.sisyphus`: 55 files, ~0.15 MB
- `data`: 8 files, ~0.11 MB
- `reports`: 33 files, ~0.06 MB

## Canonical identity artifacts detected

Primary canonical candidate (present locally and internally consistent):

- `Dataset/identity_dataset/output/full_run_codex_spark_xhigh/run_manifest.json`
- `Dataset/identity_dataset/output/full_run_codex_spark_xhigh/sft_dataset.jsonl`
- `Dataset/identity_dataset/output/full_run_codex_spark_xhigh/preference_dataset.jsonl`
- `Dataset/identity_dataset/output/full_run_codex_spark_xhigh/multimodal_manifest.json`
- `Dataset/identity_dataset/output/full_run_codex_spark_xhigh/language_manifest.json`
- `Dataset/identity_dataset/output/full_run_codex_spark_xhigh/category_manifest.json`
- `Dataset/identity_dataset/output/full_run_codex_spark_xhigh/full_internal_dataset_report_eptesicus_lumis1.pdf`

Verified local counts from canonical candidate:

- SFT rows: 100000
- Preference rows: 25000
- Multimodal rows: 9515
- Text-only rows: 90485

## Potentially confusing legacy/generated artifacts

- `reports/internal/eptesicu_labs_internal_status_report.md` and `.pdf` contain completion claims for prior flows that are not authoritative for the new local build workflow.
- `reports/train/*`, `reports/eval/*`, `reports/release_decision*.json`, `outputs/train/*`, `outputs/checkpoints/*`, `outputs/exports/*` appear to be generated from a previous training/eval pipeline.
- `Dataset/output/*` contains many sample/continued runs and a large `oss_refs` tree that can distract from the new reproducible stack.
- `Dataset/identity_dataset/output/*` contains many historical run variants besides the canonical candidate.
- Legacy implementation stack under `pipelines/`, `tests/`, `manifests/`, and portions of `configs/` is not aligned to requested Unsloth Qwen3.5 notebook build flow.

## Initial keep / archive policy

Keep in-place:

- Canonical identity pack files under `Dataset/identity_dataset/output/full_run_codex_spark_xhigh/`
- Identity generator source under `Dataset/identity_dataset/` (for traceability)

Archive (do not delete) if not part of new workspace:

- Legacy generated reports, outputs, and stale run directories
- Legacy pipeline/test/manifests/config artifacts that are superseded by the new build

Delete only disposable scratch/cache:

- Python caches (`__pycache__`) and obvious temporary scratch files when safe
