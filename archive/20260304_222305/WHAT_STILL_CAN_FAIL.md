# What Still Can Fail

Even with local validation, these risks remain until real training/eval execution:

## Data/legal

- A chosen source subset may still be legally inadmissible for commercial deployment.
- Mixed-license datasets (especially Cauldron components) may require finer subset exclusion.
- Non-commercial multilingual sources may require replacement or legal waiver.

## Data quality

- Real HF schemas can drift from expected fields and break adapters.
- Multimodal asset links may be dead/inaccessible in remote runtime.
- Dedup/quality filters may over-drop a category and skew target mix.

## Training/runtime

- RunPod environment mismatch (CUDA, torch, unsloth, trl versions) can break notebook cells.
- Effective batch sizes can still OOM depending on GPU model and sequence/image distributions.
- Resume-from-checkpoint can fail if output directory state is inconsistent.

## Evaluation/export

- OCR-heavy eval may expose hallucination regressions not visible in smoke probes.
- Export capability can differ by installed Unsloth/transformers/vLLM versions.
- Chat-template mismatch at inference can degrade outputs even if training succeeded.

## Operational

- Human path typos or missing volume mounts can invalidate runs.
- Interrupted long jobs without checkpoint discipline can waste budget.
