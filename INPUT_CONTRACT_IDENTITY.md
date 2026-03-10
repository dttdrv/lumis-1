# INPUT_CONTRACT_IDENTITY

Status: Canonical | Descriptive

The identity pack is treated as a fixed input and must be present before notebook execution.

## Preferred Canonical Files

- `Dataset/identity_dataset/output/full_run_codex_spark_xhigh/sft_dataset.jsonl`
- `Dataset/identity_dataset/output/full_run_codex_spark_xhigh/preference_dataset.jsonl`

## Accepted Alias Files

- `Dataset/identity_dataset/output/full_run_codex_spark_xhigh/identity_sft.jsonl`
- `Dataset/identity_dataset/output/full_run_codex_spark_xhigh/identity_preferences.jsonl`

Resolution order is defined once in `configs/paths.yaml` and enforced by the shared runtime helpers used by notebook 91 and `scripts/validate_identity_pack.py`.

Optional:

- `Dataset/identity_dataset/output/full_run_codex_spark_xhigh/identity_pack_report.pdf`

## Required Counts

- SFT rows: exactly **100,000**
- Preference rows: exactly **25,000**

## Required SFT Row Fields (minimum)

- `id`
- `messages`

The shared validator normalizes legacy identity rows and enforces:

- `schema_version = "1.0"`
- `source_id`
- `license`
- `thinking = "off"`
- `chat_template_kwargs.enable_thinking = false`
- canonical modality labels `text` or `image_text`

## Required Preference Row Fields (minimum)

- `id`
- `prompt`
- `chosen`
- `rejected`

The shared validator normalizes legacy preference rows and enforces:

- `source_id`
- `license`
- `thinking = "off"`
- `chat_template_kwargs.enable_thinking = false`

Notebooks `THE NOTEBOOK-sanity.ipynb` and `THE NOTEBOOK-updated.ipynb`, plus `scripts/validate_identity_pack.py`, hard-fail on missing files or count mismatches.
