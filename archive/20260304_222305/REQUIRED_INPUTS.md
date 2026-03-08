# Required Inputs

This workspace is local-only. Training is not run here by default.

## Mandatory input: canonical identity pack

Provide one directory path (default expected):

- `Dataset/identity_dataset/output/full_run_codex_spark_xhigh`

Required files in that directory:

- `sft_dataset.jsonl`
- `preference_dataset.jsonl`
- `run_manifest.json`
- `multimodal_manifest.json`

Expected baseline counts:

- `sft_dataset.jsonl`: 100000 rows
- `preference_dataset.jsonl`: 25000 rows
- Multimodal rows from manifest: 9515
- Text-only rows from manifest: 90485

## Optional local cache/input paths for open datasets

For offline or reproducible operation, optionally provide local snapshots for:

- SmolTalk / SmolTalk2
- UltraChat 200k
- WildChat-1M
- Aya dataset
- UltraFeedback cleaned preferences
- Docmatix / TextVQA / DocVQA / approved Cauldron subsets

Scripts can run in `DRY_RUN` / `SMALL_SAMPLE` mode without these snapshots.

## Environment variables

See `.env.example`. Typical requirements:

- `HF_TOKEN` (optional; needed for gated/private pulls)
- `WANDB_API_KEY` (optional; only if operator enables W&B)
- `PYTHONUNBUFFERED=1` recommended

## Runtime requirements for notebook execution (RunPod target)

- Python 3.11+
- CUDA-compatible PyTorch
- Unsloth + TRL + Transformers + Datasets stack as pinned in `requirements.txt` and `constraints.txt`
