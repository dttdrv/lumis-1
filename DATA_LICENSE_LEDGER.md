# DATA_LICENSE_LEDGER

This ledger is driven by `configs/dataset_sources_allowlist.yaml` and `configs/license_policy.yaml`.

## Enabled By Default

| Source | License | Mode | Cap (tokens) | Notes |
|---|---|---|---:|---|
| HuggingFaceH4/ultrachat_200k | MIT | hf | 180000000 | text |
| CohereLabs/aya_dataset | Apache-2.0 | hf | 140000000 | multilingual + utility |
| allenai/WildChat-4.8M | ODC-BY | hf | 220000000 | strip demographic fields |
| HuggingFaceTB/smoltalk2 | subset_specific | hf | 130000000 | only no_think subsets |
| nvidia/HelpSteer3 | CC-BY-4.0 | hf | 80000000 | preference/alignment support |
| argilla/ultrafeedback-binarized-preferences-cleaned | MIT | hf | 200000000 | primary DPO source |
| HuggingFaceM4/the_cauldron | subset_specific | hf | 30000000 | sampled only + subset allowlist |
| HuggingFaceM4/Docmatix | MIT | hf | 24000000 | sampled only |
| facebook/textvqa | CC-BY-4.0 | hf | 16000000 | sampled only |
| lmms-lab/DocVQA | Apache-2.0 | hf | 16000000 | sampled only |

## Disabled By Default

| Source | Reason |
|---|---|
| HuggingFaceM4/FineVision | subset licensing is not pre-approved; requires explicit subset allowlist + operator approval |
| nvidia/Nemotron-Post-Training-Dataset-v2 | explicit provenance/licensing warning; must remain disabled unless operator attests legal use rights |
| allenai/tulu-3-sft-mixture | optional; requires explicit operator approval + subset allowlist |
| PRIVATE_LOCAL_01 | local private template; requires full attestation fields |
| PRIVATE_LOCAL_02 | local private template; requires full attestation fields |

## PRIVATE_LOCAL Required Fields (when enabled)

- `provenance_attestation` (string)
- `license` (string)
- `redistribution_allowed` (bool)
- `pii_policy` (string)

Missing any required field while enabled is a hard failure.
