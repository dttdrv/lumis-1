# Lumis-1 Detailed Local Build Report

Status: Descriptive | Historical Snapshot

Current note as of 2026-03-08:

- The strongest completed artifact remains the canonical identity run under `Dataset/identity_dataset/output/full_run_codex_spark_xhigh/`.
- Current artifacts under `workspace/interim/*` and `workspace/final/*` are sample-scale only and must not be confused with proof of production dataset assembly.
- `workspace/runs/` still does not prove completed SFT, DPO, evaluation, or export.
- The notebook/config/runtime path is canonical; the legacy build/merge script pipeline is retired as non-canonical.

Date: 2026-03-05 00:06 (+02:00)  
Project: Lumis-1  
Organization: Eptesicus Laboratories  
Prepared by: Codex local build engineer session

## 1) Executive Summary

This repository has been converted into a local-only, operator-driven build scaffold for Lumis-1, targeting a Qwen3.5-4B training path with strict thinking-off enforcement.

The work product is intentionally non-executive for remote infrastructure: no remote pod access, no provider API calls, and no claim of completed training/export runs. The deliverables are notebooks, configs, validators, tests, and operator documentation so a human can run the pipeline manually on RunPod.

## 2) Scope Boundaries and Non-Claims

### Implemented

- Full notebook pipeline scaffolding (`00 -> 60`) with hard checks and report outputs.
- Strict source allowlist policy and private-local attestation gates.
- CoT detection/scrub hardening and final CoT zero-tolerance enforcement.
- Unsloth vision message format validation + PIL readability checks.
- Composition math (row + token) and target drift assertions.
- Export smoke utility for GGUF variant + template parity checks.

### Explicitly Not Performed

- No remote RunPod connection, no pod/volume/billing inspection.
- No end-to-end remote training completion claim.
- No model quality claim from full training/eval execution.
- No leaked or unauthorized dataset sourcing implementation.

Status statement: **unexecuted; guarded by checks** for notebooks requiring operator-run data/model steps.

## 3) Deliverables Audit

## A) Required Notebooks

- `notebooks/00_env_sanity_and_pinning.ipynb`
- `notebooks/10_validate_identity_pack.ipynb`
- `notebooks/20_build_open_dataset_mix.ipynb`
- `notebooks/30_merge_and_validate_full_dataset.ipynb`
- `notebooks/40_train_sft_unsloth_qwen35_4b.ipynb`
- `notebooks/50_train_dpo_unsloth_qwen35_4b.ipynb`
- `notebooks/60_eval_export_smoke.ipynb`

## B) Required Configs

- `configs/dataset_sources_allowlist.yaml`
- `configs/dataset_mixture.yaml`
- `configs/license_policy.yaml`
- `configs/train_sft.yaml`
- `configs/train_dpo.yaml`
- `configs/run_profiles.yaml`
- `configs/paths.yaml`
- `configs/chat_template_policy.yaml`

## C) Required Python Utilities

- `lumis1/schema.py`
- `lumis1/license_ledger.py`
- `lumis1/hf_ingest.py`
- `lumis1/filters.py`
- `lumis1/cot_scrub.py`
- `lumis1/vision_schema.py`
- `lumis1/mixing_math.py`
- `lumis1/hashing.py`
- `lumis1/export_smoke.py`
- `tests/test_schema.py`
- `tests/test_mixing_math.py`
- `tests/test_cot_scrub.py`

## D) Required Docs

- `RUNPOD_OPERATOR_CHECKLIST.md`
- `DATA_LICENSE_LEDGER.md`
- `DATASET_MANIFEST_SPEC.md`
- `OPERATOR_RUN_ORDER.md`
- `MODEL_CARD_DRAFT.md`

Additional safety contract added:

- `INPUT_CONTRACT_IDENTITY.md`

## E) Runtime Workspace Targets

Prepared and present:

- `workspace/reports/`
- `workspace/final/`
- `workspace/runs/`

## 4) Directory Hygiene and Archival Actions

Stale generated artifacts and superseded files were moved (not deleted) into:

- `archive/20260304_222305/`

Archive rationale and moved-file inventory is documented in:

- `archive/README.md`

Safety constraints respected during archival:

- User-provided PDFs were not touched.
- Identity dataset directory was not deleted or mutated.

## 5) Identity Input Contract Handling

Current strict required filenames for notebook flow:

- `Dataset/identity_dataset/output/full_run_codex_spark_xhigh/sft_dataset.jsonl` (preferred canonical name)
- `Dataset/identity_dataset/output/full_run_codex_spark_xhigh/preference_dataset.jsonl` (preferred canonical name)
- Accepted aliases for backwards compatibility: `identity_sft.jsonl`, `identity_preferences.jsonl`
- Optional: `.../identity_pack_report.pdf`

Because those exact required filenames were not present at scaffold time, contract documentation was explicitly added:

- `INPUT_CONTRACT_IDENTITY.md`

Notebook 10 enforces:

- file existence,
- row counts (100,000 SFT and 25,000 preferences),
- schema checks,
- thinking-off checks,
- CoT marker counting.

## 6) Dataset Governance and Allowlist Policy

Allowlist is strict-deny by default and includes only approved sources plus optional/disabled templates.

Enabled by default:

1. `HuggingFaceH4/ultrachat_200k` (MIT, cap 180000)
2. `CohereLabs/aya_dataset` (Apache-2.0, cap 120000)
3. `allenai/WildChat-1M` (ODC-BY, cap 200000)
4. `HuggingFaceTB/smoltalk2` (subset_specific, no_think-only policy, cap 120000)
5. `argilla/ultrafeedback-binarized-preferences-cleaned` (MIT, cap 300000)
6. `HuggingFaceM4/the_cauldron` (subset_specific, sampled only, cap 25000)
7. `HuggingFaceM4/Docmatix` (MIT, sampled only, cap 20000)
8. `facebook/textvqa` (CC-BY-4.0, sampled only, cap 12000)
9. `lmms-lab/DocVQA` (Apache-2.0, sampled only, cap 12000)

Disabled by default:

- `allenai/tulu-3-sft-mixture` (optional; explicit operator approval + subset allowlist required)
- `PRIVATE_LOCAL_01`
- `PRIVATE_LOCAL_02`

PRIVATE_LOCAL hard requirements (when enabled):

- `provenance_attestation` (string)
- `license` (string)
- `redistribution_allowed` (bool)
- `pii_policy` (string)

Any enabled PRIVATE_LOCAL entry missing required fields is a hard failure.

## 7) Thinking-Off and CoT Controls

Implemented in policy + code:

- `configs/chat_template_policy.yaml` requires `chat_template_kwargs.enable_thinking: false`.
- `lumis1/cot_scrub.py` detects markers including `<think>`, `Chain-of-thought:`, `Let's think step by step`, reasoning trace, scratchpad-like patterns.
- `lumis1/schema.py` rejects rows violating thinking-off or containing CoT markers.
- Notebook 30 computes total post-merge CoT markers and hard-fails unless zero.

## 8) Vision Validation Controls

Implemented in `lumis1/vision_schema.py`:

- Enforces Unsloth-style block content (`type: text` / `type: image`).
- Requires user messages to contain block lists for multimodal rows.
- Supports local `image_path` or base64 image bytes.
- Validates PIL decode/readability.
- Enforces image size bounds and fails unreadable/invalid samples.

## 9) Mixing Math and Target Enforcement

Implemented in `lumis1/mixing_math.py` and notebook 30:

- Row-weighted and token-weighted composition calculations.
- Category target checks: 30/20/15/15/20.
- Modality target checks: 88/12.
- Identity fixed-share check at 20% of final SFT.
- Derived non-identity multimodal requirement:
  - `(overall_mm - identity_share * identity_mm) / (1 - identity_share)`
- Hard-fail on drift beyond configured tolerances.

## 10) Notebook-Level Behavior Summary

### Notebook 00

- Asserts `transformers` major version is 5.
- Verifies `unsloth` and `unsloth_zoo` imports.
- Captures GPU info.
- Writes:
  - `workspace/reports/env_sanity.json`
  - `workspace/reports/env_freeze.txt`

### Notebook 10

- Validates identity input contract and counts.
- Samples schema validation for SFT and preference rows.
- Computes identity multimodal share.
- Writes `workspace/reports/identity_validation.json`.

### Notebook 20

- Supports `SOURCE_MODE='hf'` or `'local'`.
- Enforces allowlist-only sources.
- Applies filtering (empty user/toxic/thinking-off/CoT).
- Tracks source-level drop reasons and counts.
- Writes:
  - `workspace/interim/open_sft.jsonl`
  - `workspace/interim/open_preferences.jsonl`
  - `workspace/reports/open_corpus_build_report.json`

### Notebook 30

- Merges identity + open corpora.
- Computes row/token composition.
- Enforces target drift tolerances.
- Enforces `cot_marker_count == 0`.
- Computes hash manifest.
- Writes:
  - `workspace/final/full_sft.jsonl`
  - `workspace/final/full_preferences.jsonl`
  - `workspace/final/dataset_manifest.json`
  - `workspace/reports/full_dataset_validation.json`
  - `workspace/reports/mixture_math.json`

### Notebook 40

- Loads `configs/train_sft.yaml` and profile.
- Enforces BF16 LoRA and `load_in_4bit: false`.
- Includes first-50-step sanity switch.
- Defaults to non-execution (`RUN_TRAINING=False`).
- Writes `workspace/reports/train_sft_config_resolved.json`.

### Notebook 50

- Loads `configs/train_dpo.yaml` and profile.
- Enforces BF16 and no 4-bit training.
- Keeps optional additional preferences disabled by default.
- Defaults to non-execution (`RUN_TRAINING=False`).
- Writes `workspace/reports/train_dpo_config_resolved.json`.

### Notebook 60

- Defines eval probes for identity correctness, self-branding rate, no-image hallucination, multimodal checks.
- Supports optional local model eval execution.
- Uses export smoke utility for GGUF variants/parity when artifacts are provided.
- Writes `workspace/reports/export_smoke.json`.

## 11) Verification Evidence (Local)

Executed locally in this scaffold session:

- `python -m pytest tests/test_schema.py tests/test_mixing_math.py tests/test_cot_scrub.py`
- Result: `16 passed`.

Static integrity checks executed:

- YAML parse across all `configs/*.yaml`.
- Notebook JSON parse + code-cell compile across all `notebooks/*.ipynb`.
- Required workspace dirs existence checks.

Notes:

- Trivy MCP filesystem scan call failed in this environment (`failed to scan project`), but Trivy version lookup succeeded (`v0.68.2`).

## 12) Failure Modes and Guardrails

1. **Transformers major mismatch**  
   Guardrail: notebook 00 hard-fails if major != 5.

2. **Missing Unsloth packages**  
   Guardrail: notebook 00 import checks hard-fail.

3. **Missing identity input files**  
   Guardrail: notebook 10 file existence check + `INPUT_CONTRACT_IDENTITY.md`.

4. **Identity count drift (100k / 25k)**  
   Guardrail: notebook 10 exact count checks.

5. **Unallowlisted dataset ingestion**  
   Guardrail: allowlist enforcement in `lumis1/hf_ingest.py`.

6. **PRIVATE_LOCAL enabled without attestations**  
   Guardrail: `lumis1/license_ledger.py` hard-fail.

7. **Empty user prompts and toxic samples**  
   Guardrail: `lumis1/filters.py` drops with reason tracking.

8. **Thinking not disabled**  
   Guardrail: schema + filter checks for thinking-off and template kwargs.

9. **Residual CoT markers after processing**  
   Guardrail: notebook 30 hard-fails if merged CoT count is non-zero.

10. **Invalid multimodal schema or unreadable image**  
    Guardrail: `lumis1/vision_schema.py` validation and rejection.

11. **Category/modality drift beyond tolerance**  
    Guardrail: notebook 30 `assert_targets` checks (row + token).

12. **Non-identity multimodal share drift**  
    Guardrail: notebook 30 computes required share and hard-fails on drift.

13. **GGUF export quality mismatch**  
    Guardrail: `lumis1/export_smoke.py` checks q8_0 + q4 presence and parity/garbling indicators.

14. **Long-run terminal instability on RunPod**  
    Guardrail: operator checklist mandates SSH + tmux/nohup instead of web terminal.

## 13) Operator Execution Order (Canonical)

1. `00_env_sanity_and_pinning.ipynb`
2. `10_validate_identity_pack.ipynb`
3. `20_build_open_dataset_mix.ipynb`
4. `30_merge_and_validate_full_dataset.ipynb`
5. `40_train_sft_unsloth_qwen35_4b.ipynb`
6. `50_train_dpo_unsloth_qwen35_4b.ipynb`
7. `60_eval_export_smoke.ipynb`

## 14) Artifact Checklist Per Notebook

- 00: `env_sanity.json`, `env_freeze.txt`
- 10: `identity_validation.json`
- 20: `open_sft.jsonl`, `open_preferences.jsonl`, `open_corpus_build_report.json`
- 30: `full_sft.jsonl`, `full_preferences.jsonl`, `dataset_manifest.json`, `full_dataset_validation.json`, `mixture_math.json`
- 40: `train_sft_config_resolved.json` (+ run outputs if training enabled)
- 50: `train_dpo_config_resolved.json` (+ run outputs if training enabled)
- 60: `export_smoke.json` (+ GGUF outputs if export enabled)

## 15) Residual Risks / Open Items

- Exact identity filenames required by this scaffold may need operator-side rename/export from prior identity artifact naming.
- SmolTalk2 and The Cauldron are subset-specific; operator must maintain subset allowlists with approved licenses.
- Full quality claims remain pending until operator executes full SFT/DPO/eval/export runs and stores artifacts.

## 16) Final Status

Local build scaffold is coherent at code/config/notebook integrity level, but not proven as a completed SFT/DPO/eval/export project.  
Remote run status is intentionally not claimed.  
Training/evaluation/export completion is pending operator execution on RunPod.
