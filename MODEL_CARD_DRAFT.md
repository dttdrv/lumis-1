# MODEL_CARD_DRAFT

## Model Identity

- Model name: **Lumis-1**
- Organization: **Eptesicus Laboratories**
- Base model: **Qwen3.5-4B** (vision-capable)
- Training stack: **Unsloth only**
- Reasoning policy: **thinking disabled** (`enable_thinking: false`)

## Intended Use

General assistant behavior with multilingual and image-text utility coverage.

## Data Composition Targets

- 30% polished general assistant
- 20% real-user conversations
- 15% multilingual
- 15% utility tasks
- 20% identity + behavior

Modality overlay target:

- 88% text-only
- 12% image-text

Identity pack is fixed at 20% of final SFT mixture.

## Training Recipe (Planned)

- SFT: BF16 LoRA (no QLoRA / no 4-bit training)
- DPO: identity preferences + UltraFeedback cleaned (primary)
- Export: GGUF smoke with q8_0 and q4 candidate

## Safety & Governance

- Allowlist-only ingestion from `configs/dataset_sources_allowlist.yaml`
- PRIVATE_LOCAL entries disabled by default
- PRIVATE_LOCAL requires explicit provenance/license/redistribution/PII attestations
- CoT marker policy is hard-fail (`cot_marker_count` must be 0)

## Evaluation Plan

Notebook 60 evaluates:

- identity correctness (name/org)
- unprompted self-branding rate on neutral prompts
- vision hallucination on no-image prompts
- multimodal correctness on image prompts
- template parity and garbling checks after GGUF export

## Limitations

This repository provides local build assets and validators only. It does not claim completed remote training or remote execution.
