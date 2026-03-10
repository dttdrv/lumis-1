# OPERATOR_RUN_ORDER

Status: Canonical | Descriptive

This file defines the current notebook-first execution order only. It is not proof that the run was completed. Proof-bearing SFT, DPO, evaluation, or export claims require evidence under `workspace/runs/<run_id>/`.

## Mandatory Order

1. `THE NOTEBOOK-sanity.ipynb`
2. `THE NOTEBOOK-updated.ipynb`

## Success Artifacts By Step

- `workspace/reports/bootstrap/drive_mount.json`
- `workspace/reports/bootstrap/identity_download.json`
- `workspace/reports/bootstrap/install_strategy_and_versions.json`
- `workspace/final/full_sft.jsonl`
- `workspace/final/full_preferences.jsonl`
- `workspace/reports/final_run_report.json`
- `workspace/reports/final_run_report.md`
- `workspace/runs/<run_id>/` evidence tree when training, export, or eval is executed

## Hard Validation Rules

- Identity pack is fixed 20% of final SFT mixture.
- Final CoT marker count must be `0`.
- Row- and token-weighted category and modality targets must pass tolerance checks.
- No unallowlisted dataset may be ingested.
- PRIVATE_LOCAL entries remain disabled unless all attestation fields are provided and valid.
