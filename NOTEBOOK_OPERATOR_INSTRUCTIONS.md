# NOTEBOOK_OPERATOR_INSTRUCTIONS

Status: Canonical | Descriptive

This file explains how to run the active Lumis-1 notebook surface.

## Canonical Notebook

The only active Colab notebook is:

- `notebooks/91_colab_unified_unsloth_first.ipynb`
- `C:\Users\deyan\Projects\Lumis-1\notebooks\91_colab_unified_unsloth_first.ipynb`

No other notebook in the active tree is part of the canonical operator path.

## What Notebook 91 Actually Does

`91_colab_unified_unsloth_first.ipynb` is intended to run the active path in one Colab G4 session:

1. Create a working root under `/content/lumis1_unified` and a single evidence root under `workspace/runs/<run_id>/`
2. Recover Drive mounting safely when `/content/drive` already exists and is non-empty
3. Install Unsloth first using the official pip path, then apply only supplemental packages after the Unsloth core stack is in place
4. Materialize embedded runtime/config code locally so no repo-side YAML or `lumis1.*` imports are required upfront
5. Auto-download canonical identity files from `STnoui/lumis1-identity` with `snapshot_download` if they are not already present locally
6. Build the open dataset mix from the allowlisted HF sources and materialize concrete local image assets for supported multimodal rows
7. Merge identity plus open data into canonical outputs `workspace/final/full_sft.jsonl` and `workspace/final/full_preferences.jsonl`
8. Build a processor-ready multimodal SFT dataset in memory and fail early if the merged dataset has no concrete image rows
9. Run multimodal SFT as the main training path
10. Export GGUF first from the strongest completed artifact of the same run
11. Skip DPO by default when the run is multimodal and only text preferences are available, while recording the exact skip reason in evidence
12. Select the best available final artifact and automatically download it to the browser, or download `final_deliverables.zip` when multiple files are required

## Identity Input

Notebook 91 defaults to the public dataset repo:

- `STnoui/lumis1-identity`

The required canonical filenames are:

- `sft_dataset.jsonl`
- `preference_dataset.jsonl`

If those files are missing locally, notebook 91 downloads them automatically with `snapshot_download(..., allow_patterns=[...])` and records the result under:

- `workspace/reports/bootstrap/identity_download.json`

Manual YAML attachment is not part of the notebook 91 flow.

## Install Strategy

Notebook 91 defaults to:

- `INSTALL_STRATEGY = "unsloth_first"`

That means:

- the first serious Colab path is `pip install unsloth`
- only after Unsloth imports cleanly does the notebook install supplemental packages from the embedded requirements surface
- the notebook does not use repo-pinned-first bootstrap as the default Colab path
- the notebook records the chosen install path and package versions under `workspace/reports/bootstrap/install_strategy_and_versions.json`

## What Is Proven vs Unproven

Proven:

- Notebook 91 exists on disk.
- Notebook 91 is generated from a dedicated builder, not by lightly patching notebook 90.
- Notebook 91 compiles cell-by-cell during generation.
- The helper-layer and notebook-contract tests for notebook 91 pass locally.

Unproven:

- A real proof-bearing end-to-end Colab G4 run using notebook 91.
- Production-scale open/full dataset assembly from notebook 91.
- Completed SFT, optional DPO, eval, or GGUF export until `workspace/runs/<run_id>/` contains real evidence.
- Whether the surrogate identity image bridge is good enough for the intended multimodal claim surface.

## Important Current Limitation

Notebook 91 does not pretend multimodal DPO is stable if only text preferences are available.

Its default policy is:

- run multimodal SFT
- export GGUF from the SFT artifact first
- skip DPO with an explicit evidence record when the multimodal path only has text preferences
- continue to the final artifact selection and browser download instead of blocking the entire run late

Two important risks remain:

- identity multimodal rows still rely on surrogate local images rather than curated original screenshots/documents
- the HF multimodal source mapping is still heuristic and needs a real Colab G4 run to prove that it survives current upstream schemas

## Expected Evidence

Treat notebook 91 output as real only when the run writes evidence under:

- `workspace/runs/<run_id>/STATUS.json`
- `workspace/runs/<run_id>/SUMMARY.md`
- `workspace/runs/<run_id>/bootstrap/`
- `workspace/runs/<run_id>/dataset/`
- `workspace/runs/<run_id>/sft/`
- `workspace/runs/<run_id>/export_sft/`
- `workspace/runs/<run_id>/dpo/`
- `workspace/runs/<run_id>/export_final/`
- `workspace/runs/<run_id>/eval/`
- `workspace/runs/<run_id>/artifacts/`
- `workspace/runs/<run_id>/checksums/`

The bootstrap reports that should always exist are:

- `workspace/reports/bootstrap/drive_mount.json`
- `workspace/reports/bootstrap/identity_download.json`
- `workspace/reports/bootstrap/install_strategy_and_versions.json`

The final report outputs that should always exist are:

- `workspace/reports/final_run_report.json`
- `workspace/reports/final_run_report.md`

## Final Artifact Download Behavior

Notebook 91 automatically selects the best available final deliverable in this order:

1. post-DPO export bundle if fully successful
2. otherwise the SFT export bundle

If the best output is a single small-enough file, notebook 91 downloads that file directly.

If the best output is large or requires multiple files such as GGUF plus companion assets, notebook 91 creates and downloads:

- `final_deliverables.zip`

No manual download flag is required.
