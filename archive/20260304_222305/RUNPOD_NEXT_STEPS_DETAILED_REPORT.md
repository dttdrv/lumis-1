# RunPod Next Steps Detailed Report (Execution Critical Path)

Date: 2026-03-04
Scope: what to do next to move Lumis-1 from local-prepared state to actual training/eval execution.

## 1. Decision

Yes, the project is now at the **RunPod execution phase**.

Local build and dry-run prep are complete enough to proceed. The remaining high-value work is:

- real dataset ingestion/build in non-synthetic mode,
- staged SFT/DPO runs,
- eval and export smoke on actual runtime.

## 2. Current Readiness Snapshot

Completed locally:

- canonical identity pack validated (`100000 / 25000 / 9515 / 90485` contract)
- required configs/scripts/notebooks created
- dry-run pipeline passed end-to-end on synthetic mode
- manifest and validation outputs generated under `workspace/`

Not completed locally (expected):

- full `source_mode=hf` dataset build
- actual Unsloth training (SFT/DPO)
- real export quality verification on trained checkpoints

## 3. Mandatory Preconditions Before Spending GPU

1. Data/legal decisions
- Resolve `review_required` and `subset_review_required` sources before full ingest:
  - notably non-commercial or mixed-license datasets.
- If not approved, disable/replace those sources in `configs/dataset_mixture.yaml`.

2. Runtime and storage
- Ensure sufficient storage for dataset + checkpoints + exports.
- Use fallback profile if VRAM is below target profile assumptions.

3. Environment
- Install from:
  - `requirements.txt`
  - `constraints.txt`
- Confirm imports: `unsloth`, `transformers`, `trl`, `datasets`, `torch`.

## 4. Exact Execution Order on RunPod

1. Validate identity input
- Notebook: `notebooks/10_validate_identity_pack.ipynb`
- Gate: strict validation must pass.

2. Build open corpus (real mode)
- Notebook: `notebooks/20_build_open_dataset_mix.ipynb`
- Set `SOURCE_MODE='hf'`
- Start with `DRY_RUN=True`, then full run.
- Gate: `open_corpus_build_report.json` shows:
  - source counts before/after,
  - drop counters,
  - non-identity modality math near target.

3. Merge and validate full warehouse
- Notebook: `notebooks/30_merge_and_validate_full_dataset.ipynb`
- Gate: strict full validation pass in `workspace/reports/full_dataset_validation.json`.

4. Freeze dataset for training
- Keep these immutable for training:
  - `workspace/final/full_sft.jsonl`
  - `workspace/final/full_preferences.jsonl`
  - `workspace/final/dataset_manifest.json`

5. Train SFT stages (A/B/C; E optional)
- Notebook: `notebooks/40_train_sft_unsloth_qwen35_4b.ipynb`
- Use config: `configs/train_sft_qwen35_4b_unsloth.yaml`
- Start with intended profile, fallback if OOM.
- Gate: stage manifests/checkpoints written under `workspace/runs/sft`.

6. Train DPO stage (optional after SFT success)
- Notebook: `notebooks/50_train_dpo_unsloth_qwen35_4b.ipynb`
- Use config: `configs/train_dpo_qwen35_4b_unsloth.yaml`
- Gate: DPO run manifest/checkpoints under `workspace/runs/dpo`.

7. Eval/export smoke
- Notebook: `notebooks/60_eval_export_smoke.ipynb`
- Gate: smoke report + export capability records.

## 5. Stop Conditions (Do Not Continue Blindly)

Stop and fix before next stage if any of these occur:

- identity validation fails;
- full dataset validation strict fails;
- modality or identity share drift outside configured tolerance;
- repeated OOM despite fallback profile;
- checkpoint writes fail or resume path invalid;
- license/admissibility unresolved for enabled source.

## 6. Expected Artifacts to Return After RunPod Session

Minimum return package:

- `workspace/reports/identity_validation.json`
- `workspace/reports/open_corpus_build_report.json`
- `workspace/reports/merge_full_warehouse_report.json`
- `workspace/reports/full_dataset_validation.json`
- `workspace/final/dataset_manifest.json`
- SFT run manifest(s) + checkpoint summary under `workspace/runs/sft`
- DPO run manifest(s) + checkpoint summary under `workspace/runs/dpo` (if executed)
- eval/export smoke outputs from notebook 60

## 7. Practical First Run Strategy

1. Do a full notebook pass with small bounds first:
- `DRY_RUN=True`, `SMALL_SAMPLE=True`
- verify paths and output directories.

2. Then promote to full run:
- disable dry-run flags,
- keep same output roots,
- enable resume checkpoints from start.

## 8. Recommended Operator Response Format After Each Stage

For each completed stage, log:

- exact notebook name and timestamp,
- config profile used (`default_96gb` or `safe_fallback`),
- rows processed and key metric outputs,
- whether stage gate passed/failed,
- artifact paths produced.
