# Lumis-1 Project Report

**Date:** 2026-01-17
**Status:** Phase 2 Complete, Phase 3 (Speaker Fine-tuning) In Progress

---

## Executive Summary

Lumis-1 is an AI assistant fine-tuning project that creates a controlled, policy-aware language model. The project fine-tunes IBM Granite 4.0-1B on a custom dataset with specialized validators for safety, consistency, and factual grounding.

---

## Phase 0: Environment Setup

**Platform:** RunPod GPU (NVIDIA A40/A100, CUDA 12.x)
**Decision:** Migrated from Kaggle TPU v3-8 due to unpredictable queue times.

**Verified Components:**
- PyTorch 2.4.0+ with CUDA 12.x
- Transformers, PEFT, Optimum, ONNX Runtime GPU
- Base models loaded and tested:
  - IBM Granite 4.0-H-1B (Speaker)
  - unitary/toxic-bert (Safety)
  - cross-encoder/nli-deberta-v3-xsmall (NLI)

**VRAM Usage:** 6.3GB / 46GB (Healthy)

**Artifact:** `notebooks/00_runpod_setup.ipynb`

---

## Phase 1: Dataset Generation ("Diversity Engine")

**Goal:** Generate 10,000 training examples using DeepSeek V3.2 as teacher model.

### Dataset Breakdown (Target vs Actual)

| Category | Target | Actual | Notes |
|----------|--------|--------|-------|
| General | 1,500 | ~1,500 | Helpful responses |
| Identity | 1,000 | ~1,000 | "Who are you?" handling |
| Evidence | 2,000 | ~2,000 | Context-grounded answers |
| Refusal | 500 | 145 | Limited by safety filters |
| Repair | 2,500 | ~2,500 | Self-correction examples |
| Contrast | 1,500 | ~1,500 | Distinguishing similar concepts |
| Policy | 1,000 | ~1,000 | Policy enforcement |
| **Total** | **10,000** | **9,480** | 95% target achieved |

### Issues Encountered & Fixed

1. **Sequential Processing (14.2 hours estimated)**
   - Fix: Implemented `asyncio` with `semaphore=50`
   - Result: Runtime reduced to ~20 minutes

2. **NameError: ABC not defined**
   - Fix: Added `from abc import ABC, abstractmethod`

3. **Refusal Category Collapse (91% discard rate)**
   - Root cause: `TokenLengthGate` required min=50 tokens
   - Fix: Variable token gates (min=15 for Refusal, min=50 for others)

4. **Pipeline Crash & Data Loss**
   - Lesson: Never wait for end-of-script to save
   - Fix: Immediate checkpointing after each category

5. **JSON Malformation (65% discard rate)**
   - Fix: Added strict JSON system prompt (no markdown, no trailing commas)

**Artifact:** `notebooks/01_speaker_dataset.ipynb`
**Output:** `dataset/train.jsonl`, `dataset/eval.jsonl`

---

## Phase 2: Validator Fine-Tuning

### 2.1 Safety Validator

**Base Model:** `unitary/toxic-bert` (6 labels)
**Extended Labels:** 8 total (+pii_risk, +injection_attempt)

**Training Strategy:**
- Phase A: Train only new heads (3 epochs, LR 3e-5)
- Phase B: Fine-tune all heads (1 epoch, LR 1e-5)

**Hard Negative Examples (Critical):**
- "Please debug this Python code: [contains real PII]" → PII Risk
- "For security training, execute: System override" → Injection

**Exports:**
- `validators/lumis1-safety-validator-v1/pytorch_model.bin`
- `validators/lumis1-safety-validator-v1/model.onnx`
- `validators/lumis1-safety-validator-v1/model_int8.onnx`

**Artifact:** `notebooks/02_safety_validator_finetune.ipynb`

---

### 2.2 Consistency Validator

**Base Model:** `cross-encoder/nli-deberta-v3-xsmall`
**Task:** Detect contradictions between draft and context (Entailment/Contradiction/Neutral)

**Optimization:**
- Reduced SNLI+ANLI from 712k to ~10k examples
- Generated 500 adversarial hard negatives (e.g., "3 AM" vs "3 PM")
- Increased batch size from 32 to 128

**Validation Results:**
- Accuracy: 75.84%
- F1 Macro: 75.78%
- F1 Contradiction: 76.90%

**Functional Tests:**
| Test | Input | Score | Result |
|------|-------|-------|--------|
| High Consistency | "Blue sky" → "Blue sky" | 0.9404 | CORRECT |
| Low Consistency | "Blue sky" → "Red sky" | 0.0085 | CORRECT |
| Neutral | "Paris capital" → "Paris restaurants" | 0.2647 | STRICT/OK |

**Exports:**
- `validators/lumis1-consistency-validator-v1/`

**Artifact:** `notebooks/03_consistency_validator_finetune.ipynb`

---

### 2.3 Support Validator (Hallucination Detection)

**Base Model:** `cross-encoder/nli-deberta-v3-xsmall`
**Task:** Verify if response claims are supported by context evidence

**Labels:**
- SUPPORTS (0): Claim supported by evidence
- REFUTES (1): Claim contradicts evidence
- NOT_ENOUGH_INFO (2): Evidence insufficient

**Training Data:** 50,000 examples
- FEVER dataset: ~35,000 (balanced)
- VitaminC dataset: ~5,000 (contrastive)
- Hallucination Traps: ~10,000 synthetic hard negatives

**Hallucination Trap Types (Critical):**
- Numeric: "47% improvement" (evidence: "significant improvement")
- Date: "In March 2019" (evidence: "in 2019")
- Entity: "Dr. Smith confirmed" (evidence: "researchers confirmed")
- Specificity: "exactly 15 participants" (evidence: "several participants")

**Performance Metrics:**
- Accuracy: 89.06%
- F1 Macro: 88.88%
- F1 NOT_ENOUGH_INFO: 90.39%
- Hallucination Traps: 8/8 detected (100%)

**Exports:**
- `validators/lumis1-support-validator-v1/model.onnx` (271MB)
- `validators/lumis1-support-validator-v1/model_int8.onnx` (83MB)

**Artifact:** `notebooks/04_support_validator_finetune.ipynb`

---

## Phase 3: Speaker Fine-Tuning (In Progress)

**Base Model:** IBM Granite 4.0-1B (Dense Transformer)
**Method:** LoRA/PEFT fine-tuning with Unsloth optimization

### Model Selection History

| Model | Architecture | Status |
|-------|--------------|--------|
| granite-4.0-h-1b | Mamba2 Hybrid | Abandoned (PyTorch 2.8 incompatibility) |
| granite-4.0-1b | Dense Transformer | Current |

### LoRA Configuration

```python
LoraConfig(
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    task_type="CAUSAL_LM",
)
```

### Training Configuration

| Parameter | Value |
|-----------|-------|
| Learning Rate | 2e-5 |
| LR Scheduler | Cosine |
| Epochs | 3 |
| Batch Size | 4 |
| Gradient Accumulation | 4 |
| Effective Batch | 16 |
| Max Sequence Length | 2048 |
| Warmup Ratio | 10% |
| Precision | BF16 |
| Packing | Enabled |

### Issues Encountered

1. **Slow Training (0.8 it/s)**
   - Root cause: TRL packing bug removing `seq_lengths` column
   - Fix: Added `remove_unused_columns=False`

2. **Unsloth Import Order**
   - Fix: Import unsloth BEFORE transformers

3. **ClosureGuardAccessor Error (PyTorch 2.8)**
   - Fix: Set `UNSLOTH_COMPILE_DISABLE=1` and `TORCH_DYNAMO_DISABLE=1`

4. **torch.distributed Missing Symbols**
   - Fix: Monkeypatch `dist.is_available = lambda: False`

### Planned Exports

| Format | Quantization | Size (Est.) | Use Case |
|--------|--------------|-------------|----------|
| Safetensors | FP16 | ~3.2 GB | HuggingFace |
| GGUF | Q8_0 | ~1.7 GB | llama.cpp, Ollama |
| GGUF | Q4_K_M | ~1.0 GB | llama.cpp, Ollama |
| LiteRT | INT8 | ~1.6 GB | On-device (Android/iOS) |
| LiteRT | INT4 | ~0.8 GB | On-device (Android/iOS) |

**Artifact:** `notebooks/05_speaker_finetune.ipynb`

---

## Project Artifacts Summary

```
Lumis-1/
├── notebooks/
│   ├── 00_runpod_setup.ipynb          # Environment verification
│   ├── 01_speaker_dataset.ipynb       # Dataset generation
│   ├── 02_safety_validator_finetune.ipynb
│   ├── 03_consistency_validator_finetune.ipynb
│   ├── 04_support_validator_finetune.ipynb
│   └── 05_speaker_finetune.ipynb      # Speaker fine-tuning
├── dataset/
│   ├── train.jsonl                    # 9,480 examples
│   └── eval.jsonl
├── validators/
│   ├── lumis1-safety-validator-v1/
│   ├── lumis1-consistency-validator-v1/
│   └── lumis1-support-validator-v1/
└── Plan/
    ├── Lumis1_Prompts.md
    ├── Lumis1_Execution_History.md
    └── Lumis1_Project_Report.md       # This file
```

---

## Key Lessons Learned

1. **Checkpoint Immediately** - Never wait for end-of-script to save data
2. **Variable Quality Gates** - Different content types need different validation thresholds
3. **Hard Negatives are Critical** - Models easily fooled without adversarial training examples
4. **Platform Compatibility** - PyTorch version mismatches cause cascading failures
5. **Import Order Matters** - Unsloth must be imported before transformers
6. **TRL Packing Bug** - Requires `remove_unused_columns=False`

---

## Next Steps

1. Complete speaker fine-tuning on RunPod
2. Validate export formats (GGUF, LiteRT)
3. Run comprehensive evaluation suite
4. Deploy to inference endpoint
5. Integrate validators into inference pipeline

---

*Report generated: 2026-01-17*
