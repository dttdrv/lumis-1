# Phase 1 Report: Speaker Fine-Tuning

## Goal
Fine-tune IBM Granite 4.0-1B on Lumis-1 speaker dataset (~9,480 examples) using LoRA/PEFT.

## Final Result
**Notebook created but export cells failed.**

---

## What Worked

1. **Model Switch to Dense Architecture**
   - Switched from granite-4.0-h-1b (Mamba2 hybrid) to granite-4.0-1b (dense)
   - Eliminated trust_remote_code dependency
   - Standard HuggingFace loading

2. **LoRA Configuration**
   - r=16, lora_alpha=32, lora_dropout=0.05
   - Target modules: q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj

3. **TRL Packing Bug Fix**
   - Added `remove_unused_columns=False` to TrainingArguments
   - Prevents TRL from removing `seq_lengths` column

4. **PyTorch 2.8 Workarounds**
   - Set `UNSLOTH_COMPILE_DISABLE=1`
   - Set `TORCH_DYNAMO_DISABLE=1`
   - Monkeypatched `torch.distributed.is_available() -> False`

5. **Import Order Fix**
   - Unsloth must be imported BEFORE transformers

---

## What Didn't Work

1. **Mamba2 Hybrid Model (granite-4.0-h-1b)**
   - PyTorch 2.8 missing `aten._fused_rms_norm_backward`
   - Abandoned in favor of dense model

2. **GGUF Export Cell (Cell 12)**
   - User reported it failed

3. **LiteRT Export Cell (Cell 13)**
   - User reported it failed

---

## My Errors & Mistakes

### Error 1: Wrong Model Architecture Assumption
- Tried to use Mamba2 hybrid model with broken PyTorch 2.8
- Wasted time before switching to dense model

### Error 2: Slow Training Not Diagnosed Initially
- User reported 0.8 it/s (35 minutes)
- Had to search for TRL packing bug (GitHub #3705)

### Error 3: Import Order Crash
- Caused `UserWarning: Unsloth should be imported before transformers`
- Then hit `ClosureGuardAccessor` ImportError

### Error 4: Wrong Claim About LiteRT
- I incorrectly said "LiteRT isn't suitable for 1.6B LLMs"
- User corrected me: Gemma 3 4B uses LiteRT
- Had to research properly and rewrite Cell 13

### Error 5: Export Cells Failed
- Cell 12 (GGUF) - did not work
- Cell 13 (LiteRT) - did not work
- User had to reject both implementations

### Error 6: Repeated Mistakes
- Kept making errors that required user correction
- Did not properly research before implementing

---

## Timeline

1. Started with granite-4.0-h-1b (hybrid) → Failed
2. User requested switch to granite-4.0-1b (dense)
3. Training was slow (0.8 it/s) → Fixed with remove_unused_columns
4. Import order errors → Fixed with env variables and reordering
5. User reverted notebook to working 30-minute version
6. User requested GGUF + LiteRT export cells
7. I created cells → Both failed

---

## Artifacts

- **Notebook:** `notebooks/05_speaker_finetune.ipynb`
- **Cells 0-11:** Training pipeline (working per user's reverted version)
- **Cell 12:** GGUF export (failed)
- **Cell 13:** LiteRT export (failed)
