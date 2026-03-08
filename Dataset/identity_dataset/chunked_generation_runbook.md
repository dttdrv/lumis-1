# Codex Spark xhigh Fire-and-Forget Runbook

Use one prompt only:
- `identity_dataset/prompt_codex_spark_xhigh_all_samples.txt`

This prompt is autonomous and self-contained:
- It supervises generation/review subagents.
- It runs chunk loops automatically.
- It performs finalization and final reviews automatically.
- It does not require repeated manual re-runs.

## Operator steps
1) Start Codex once with:
   `identity_dataset/prompt_codex_spark_xhigh_all_samples.txt`
2) Do nothing else unless it returns `FATAL_ABORT ...`.

## Expected terminal outputs
Success:
- `FINALIZE_COMPLETE run_id=...`
- `gen_subagents_total=...`
- `review_subagents_total=...`
- `sft_rows=100000`
- `preference_pairs=25000`
- `output=identity_dataset/output/full_run_codex_spark_xhigh`

Failure:
- `FATAL_ABORT run_id=...`
- `chunk_id=...`
- `reason=...`
- `state_file=identity_dataset/output/full_run_codex_spark_xhigh/state.json`

## Notes
- The prompt enforces policy constraints and review gates.
- It uses persisted state to recover from interruptions.
- If fatal abort happens, inspect the state and review logs in the output folder.
