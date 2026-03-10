# NOTEBOOK_OPERATOR_INSTRUCTIONS

Status: Canonical | Descriptive

This file explains how to run the active Lumis-1 notebook surface.

## Active Notebooks

The active Colab notebooks are:

- `THE NOTEBOOK-sanity.ipynb`
- `C:\Users\deyan\Projects\Lumis-1\THE NOTEBOOK-sanity.ipynb`
- `THE NOTEBOOK-updated.ipynb`
- `C:\Users\deyan\Projects\Lumis-1\THE NOTEBOOK-updated.ipynb`

Use the sanity notebook for a short proving pass and the updated notebook for the full run.

## What Notebook 91 Actually Does

`THE NOTEBOOK-sanity.ipynb` and `THE NOTEBOOK-updated.ipynb` run the same active path in one Colab G4 session:

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

## Sanity vs Full

- `THE NOTEBOOK-sanity.ipynb` runs the bounded sanity SFT step budget from `configs/train_sft.yaml`
- `THE NOTEBOOK-updated.ipynb` runs the full configured SFT step budget
- there is no `LUMIS1_SANITY_ONLY` switch in the notebook surface anymore

## Install Strategy

Both notebook surfaces default to:

- `INSTALL_STRATEGY = "unsloth_first"`

That means:

- the first serious Colab path is `pip install unsloth`
- only after Unsloth imports cleanly does the notebook install supplemental packages from the embedded requirements surface
- the notebook does not use repo-pinned-first bootstrap as the default Colab path
- the notebook records the chosen install path and package versions under `workspace/reports/bootstrap/install_strategy_and_versions.json`

## What Is Proven vs Unproven

Proven:

- Both notebook surfaces exist on disk.
- Both notebook surfaces are generated from a dedicated builder, not by lightly patching notebook 90.
- Both notebooks compile cell-by-cell during generation.
- The helper-layer and notebook-contract tests for both notebooks pass locally.

Unproven:

- A real proof-bearing end-to-end Colab G4 run using either notebook surface.
- Production-scale open/full dataset assembly from the full notebook surface.
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
