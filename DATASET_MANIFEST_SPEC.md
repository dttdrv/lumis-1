# DATASET_MANIFEST_SPEC

Status: Canonical | Descriptive

Required output file: `workspace/final/dataset_manifest.json`

This manifest describes the current dataset artifacts only. It is not proof of completed SFT, DPO, evaluation, or export. Those claims require evidence under `workspace/runs/<run_id>/`.

## Required top-level keys

- `schema_version`
- `project`
- `created_utc`
- `paths`
- `sha256`
- `counts`
- `shares`
- `targets`
- `validations`

## `paths`

- `full_sft`
- `full_preferences`
- `validation_report`

## `sha256`

- `full_sft`
- `full_preferences`

All hashes are computed from bytes on disk.

## `counts`

- `sft_rows_total`
- `preferences_rows_total`
- `identity_sft_rows`
- `identity_preference_rows`
- `invalid_sft_rows`
- `sft_tokens_total`
- `identity_sft_tokens`
- `open_sft_tokens`

## `shares`

- `row_weighted.category`
- `row_weighted.modality`
- `token_weighted.category`
- `token_weighted.modality`
- `token_weighted.identity_token_share`
- `identity_multimodal_share_tokens`
- `required_non_identity_multimodal_share_tokens`
- `actual_non_identity_multimodal_share_tokens`

## `targets`

- `category`
- `modality`
- `tolerance`
- `identity_token_share`

## `validations`

- `cot_marker_count`
- `cot_marker_count_zero`
- `no_invalid_rows`
- `token_category_targets_within_tolerance`
- `token_modality_targets_within_tolerance`
- `identity_token_share_exact`
- `non_identity_multimodal_share_within_tolerance`
- `preferences_nonempty`
- `row_drifts_secondary`

## Hard-fail criteria

Manifest generation must fail if:

- any required artifact path is missing
- any hash cannot be computed
- the validation report cannot be built or loaded

The dataset-prep notebook and validator decide whether the current artifacts are acceptable. The manifest itself is descriptive and reflects the paired validation report.
