# RUNPOD Operator Checklist

Status: Canonical | Descriptive

This checklist describes the intended operator workflow only. It is not execution proof. Treat a run as complete only when `workspace/runs/<run_id>/` contains the required evidence files.

## Required Infrastructure

- Attach a network volume and mount it at `/workspace` before running notebooks.
- Use SSH for long-running work; do not rely on the RunPod web terminal for long training jobs.
- Use `tmux` or `nohup` so long-running work survives session drops.

## Required Inputs

Preferred canonical identity files:

- `Dataset/identity_dataset/output/full_run_codex_spark_xhigh/sft_dataset.jsonl`
- `Dataset/identity_dataset/output/full_run_codex_spark_xhigh/preference_dataset.jsonl`

Accepted aliases:

- `Dataset/identity_dataset/output/full_run_codex_spark_xhigh/identity_sft.jsonl`
- `Dataset/identity_dataset/output/full_run_codex_spark_xhigh/identity_preferences.jsonl`

Optional:

- `Dataset/identity_dataset/output/full_run_codex_spark_xhigh/identity_pack_report.pdf`

If the identity files are missing, stop and satisfy `INPUT_CONTRACT_IDENTITY.md` first.

## Preflight Commands

- `python -m pip install -r requirements.txt`
- `python -m pip install -c constraints.txt -r requirements.txt`
- `python -m pytest tests/test_schema.py tests/test_mixing_math.py tests/test_cot_scrub.py`

## Notebook Execution Order

Run exactly:

1. `notebooks/00_env_sanity_and_pinning.ipynb`
2. `notebooks/10_validate_identity_pack.ipynb`
3. `notebooks/20_build_open_dataset_mix.ipynb`
4. `notebooks/30_merge_and_validate_full_dataset.ipynb`
5. `notebooks/40_train_sft_unsloth_qwen35_4b.ipynb`
6. `notebooks/50_train_dpo_unsloth_qwen35_4b.ipynb`
7. `notebooks/60_eval_export_smoke.ipynb`

## Stop Conditions

Stop immediately if any of the following occur:

- `transformers` major version is not `5`
- `chat_template_kwargs.enable_thinking` is not `false`
- any unallowlisted dataset is requested
- any PRIVATE_LOCAL source is enabled without required attestations
- `cot_marker_count` after final merge is not `0`
- dataset target drift exceeds configured tolerance

## Proof-Bearing Run Evidence

Any real SFT, DPO, evaluation, or export claim must write evidence under `workspace/runs/<run_id>/` with:

- `STATUS.json`
- `SUMMARY.md`
- `config_snapshot/`
- `commands/`
- `environment/`
- `logs/`
- `reports/`
- `artifacts/`
- `checksums/`

Notebook presence, sample outputs under `workspace/final/`, or root-level reports are not sufficient proof of completed training/eval/export.
