# PROJECT_TIME_CAPSULE

## Snapshot 2026-03-08 08:00:56 +02:00 — Session rehab-20260308-01

### Canonical execution path
- `configs/*.yaml`
- `notebooks/00_env_sanity_and_pinning.ipynb`
- `notebooks/10_validate_identity_pack.ipynb`
- `notebooks/20_build_open_dataset_mix.ipynb`
- `notebooks/30_merge_and_validate_full_dataset.ipynb`
- `notebooks/40_train_sft_unsloth_qwen35_4b.ipynb`
- `notebooks/50_train_dpo_unsloth_qwen35_4b.ipynb`
- `notebooks/60_eval_export_smoke.ipynb`
- `lumis1/*`
- `workspace/reports/*`
- `Dataset/identity_dataset/output/full_run_codex_spark_xhigh/`

### Proven claims
- The identity run `identity-20260303T162023Z` completed at 100,000 SFT rows and 25,000 preference pairs.
- `workspace/reports/identity_validation.json` validates the canonical identity artifact.
- Unit tests, YAML parsing, notebook JSON validation, and active-path audit passed on 2026-03-06.
- Current Trivy evidence places active HIGH/CRITICAL findings at 0 and archive-only findings at 63.

### Unproven claims
- Production-scale open/full dataset assembly.
- Completed SFT, DPO, evaluation, or export.
- Manual RunPod completion.
- `workspace/runs/` as proof of any completed training or export stage.

### Current blockers
- Script/config drift in active wrappers.
- Manifest spec drift versus actual generated manifest files.
- Identity path/documentation drift versus the actual canonical artifact filenames.

### Active defects
- `scripts/validate_identity_pack.py` expects obsolete `identity` config keys.
- `scripts/validate_full_dataset.py` expects obsolete `bucket_targets` config keys.
- `scripts/render_dataset_manifest.py` emits a stale manifest contract.
- `scripts/build_open_corpus.py` and `scripts/merge_full_warehouse.py` reflect a non-authoritative legacy path.

### Current risk register
- A reader could mistake sample outputs for proof of production completion.
- Docs and scripts can drift again unless shared runtime helpers become the single source of truth.
- Notebook JSON edits are brittle without validation.

### Evidence-bearing artifacts
- `Dataset/identity_dataset/output/full_run_codex_spark_xhigh/run_manifest.json`
- `Dataset/identity_dataset/output/full_run_codex_spark_xhigh/state.json`
- `Dataset/identity_dataset/output/full_run_codex_spark_xhigh/review_report.json`
- `Dataset/identity_dataset/output/full_run_codex_spark_xhigh/quality_review_report.md`
- `workspace/reports/identity_validation.json`

### Most trustworthy files
- `configs/dataset_mixture.yaml`
- `configs/paths.yaml`
- `notebooks/10_validate_identity_pack.ipynb`
- `notebooks/30_merge_and_validate_full_dataset.ipynb`
- `PM_REPOSITORY_AUDIT_2026-03-06.md`

### Least trustworthy / stale files
- `scripts/build_open_corpus.py`
- `scripts/merge_full_warehouse.py`
- `scripts/validate_identity_pack.py`
- `scripts/validate_full_dataset.py`
- `scripts/render_dataset_manifest.py`
- `scripts/resume_train_local.sh`
- `workspace/final/full_dataset_manifest.json`

### What changed in understanding during this session
- The canonical identity artifact uses `sft_dataset.jsonl` and `preference_dataset.jsonl` as the primary proven files.
- Notebook 50 uses a generic TRL `DPOTrainer` path, so its current wording overstates Unsloth specificity.
- Sample outputs under `workspace/final/*` still carry legacy row-shape conventions and require compatibility normalization.

### Artifacts produced this session
- `PROJECT_CHANGELOG_DETAILED.md`
- `PROJECT_TIME_CAPSULE.md`

### Most recent validation status
- Last known repo-wide verification state is from 2026-03-06 and remains the current trusted baseline.

### Last known good commands
```bash
# python -m pytest tests/test_schema.py tests/test_mixing_math.py tests/test_cot_scrub.py
# python scripts/audit_active_generation_paths.py --output workspace/reports/verification_20260306/active_generation_audit_fresh.json
```

### Exact next step for the next agent
- Extract shared runtime helpers for identity validation, manifest generation, full-dataset validation, and run evidence, then use them to repair the kept wrappers and notebooks.

## Snapshot 2026-03-08 08:48:56 +02:00 — Session rehab-20260308-01

### Canonical execution path
- `configs/*.yaml`
- `notebooks/00_env_sanity_and_pinning.ipynb`
- `notebooks/10_validate_identity_pack.ipynb`
- `notebooks/20_build_open_dataset_mix.ipynb`
- `notebooks/30_merge_and_validate_full_dataset.ipynb`
- `notebooks/40_train_sft_unsloth_qwen35_4b.ipynb`
- `notebooks/50_train_dpo_unsloth_qwen35_4b.ipynb`
- `notebooks/60_eval_export_smoke.ipynb`
- `lumis1/*`
- `workspace/reports/*`
- `Dataset/identity_dataset/output/full_run_codex_spark_xhigh/`

### Proven claims
- The identity run `identity-20260303T162023Z` remains the strongest completed artifact at 100,000 SFT rows and 25,000 preference rows.
- `workspace/reports/identity_validation.json` now resolves and validates the canonical identity filenames `sft_dataset.jsonl` and `preference_dataset.jsonl`.
- Kept script wrappers (`validate_identity_pack`, `validate_full_dataset`, `render_dataset_manifest`) now execute against shared runtime helpers instead of stale schema assumptions.
- Deprecated dataset-build wrappers now fail explicitly and route operators to the canonical notebooks.
- `workspace/final/dataset_manifest.json` and `workspace/reports/full_dataset_validation.json` are now regenerated from the current canonical manifest/validation runtime.
- Unit tests pass at `31 passed` and notebook JSON/code compilation succeeds after the rehab changes.

### Unproven claims
- Any completed SFT run.
- Any completed DPO run.
- Any completed evaluation run.
- Any completed export run.
- Any claim that `workspace/runs/` already contains completed training/eval/export evidence.

### Current blockers
- There is still no real proof-bearing run under `workspace/runs/<run_id>/`; the contract exists but has not been exercised with an actual training/eval/export execution.
- Sample-scale `workspace/final/*` outputs still cannot be treated as production mixture proof.

### Active defects
- No known active-path code defects remain from the reviewed truth/parity issues.
- Remaining gaps are execution-evidence gaps, not validator/manifester/path-resolution drift defects.

### Current risk register
- A future operator could still overread notebook presence as proof unless they check for populated `workspace/runs/<run_id>/STATUS.json` and accompanying artifacts.
- Notebook training/eval execution has not been run in this pass, so runtime dependency failures remain possible outside the tested static surface.
- Legacy archive materials still mention old run layouts and must remain clearly historical.

### Current evidence-bearing artifacts
- `Dataset/identity_dataset/output/full_run_codex_spark_xhigh/run_manifest.json`
- `Dataset/identity_dataset/output/full_run_codex_spark_xhigh/state.json`
- `Dataset/identity_dataset/output/full_run_codex_spark_xhigh/review_report.json`
- `Dataset/identity_dataset/output/full_run_codex_spark_xhigh/quality_review_report.md`
- `workspace/reports/identity_validation.json`
- `workspace/reports/full_dataset_validation.json`
- `workspace/final/dataset_manifest.json`

### Most trustworthy files
- `PROJECT_BRIEF.md`
- `STATE.yaml`
- `configs/paths.yaml`
- `configs/dataset_mixture.yaml`
- `configs/train_sft.yaml`
- `configs/train_dpo.yaml`
- `lumis1/identity_pack.py`
- `lumis1/full_dataset.py`
- `lumis1/run_evidence.py`

### Least trustworthy / stale files
- `workspace/final/full_dataset_manifest.json`
- historical archive planning docs under `archive/`
- any future `workspace/runs/<run_id>/` directory that exists without populated evidence files

### What changed in understanding during this session
- Notebook 30 needed shared sample-mode merge logic, not just sample-mode validation.
- Manifest regeneration must be input-driven every time; cached validation reuse is not acceptable for a proof-bearing surface.
- The run-evidence contract had to be config-driven and applied to SFT and DPO, not only eval/export, to avoid a new round of path drift.

### Artifacts produced this session
- `PROJECT_CHANGELOG_DETAILED.md`
- `PROJECT_TIME_CAPSULE.md`
- `workspace/reports/identity_validation.json`
- `workspace/reports/full_dataset_validation.json`
- `workspace/final/dataset_manifest.json`
- `workspace/final/dataset_manifest.md`

### Most recent validation status
- `python -m pytest -q` passed with `31 passed`.
- Notebook JSON/code compilation passed for all active notebooks.
- `python scripts/validate_identity_pack.py --strict` passed.
- `python scripts/validate_full_dataset.py --allow-small-sample --strict` passed.
- `python scripts/render_dataset_manifest.py --allow-small-sample` passed.
- `workspace/runs/` contains no completed proof-bearing SFT/DPO/eval/export runs at the end of this session.

### Last known good commands
```bash
# python -m pytest -q
# python scripts/validate_identity_pack.py --strict
# python scripts/validate_full_dataset.py --allow-small-sample --strict
# python scripts/render_dataset_manifest.py --allow-small-sample
```

### Exact next step for the next agent
- Run notebook 40 with `RUN_TRAINING=True` into the configured `workspace/runs/manual-sft/artifacts/sft_model`, confirm evidence files populate under `workspace/runs/manual-sft/`, then flow that output through notebook 50 and notebook 60 to replace the current unproven training/eval/export state with real run evidence.

## Snapshot 2026-03-08 09:15:21 +02:00 — Session rehab-20260308-02

### Canonical execution path
- `configs/*.yaml`
- `notebooks/00_env_sanity_and_pinning.ipynb`
- `notebooks/10_validate_identity_pack.ipynb`
- `notebooks/20_build_open_dataset_mix.ipynb`
- `notebooks/30_merge_and_validate_full_dataset.ipynb`
- `notebooks/40_train_sft_unsloth_qwen35_4b.ipynb`
- `notebooks/50_train_dpo_unsloth_qwen35_4b.ipynb`
- `notebooks/60_eval_export_smoke.ipynb`
- `lumis1/*`

### Proven claims
- The active repo is coherent enough to support a sequential orchestration surface.
- Unsloth now has an official GGUF save path (`save_pretrained_gguf`), so active-path GGUF export can be implemented without relying on archive-only scripts.
- Current training notebooks still require runtime/output overrides to be comfortable for a single Colab notebook.

### Unproven claims
- That the current repo can already do end-to-end GGUF export without additional implementation.
- That the current notebook set is ergonomic enough for single-notebook Colab operation.

### Current blockers
- No active GGUF export implementation yet.
- No single notebook yet that handles Drive mount, identity input path, sequential overrides, export, and download.

### Active defects
- Notebook 60 verifies exports but does not create them.
- Notebook 40 and notebook 50 still rely on config-owned output directories rather than deriving them directly from a run prefix in one orchestration flow.

### Current risk register
- Colab dependency drift may break pinned installs unless the notebook handles fallback cleanly.
- A one-notebook surface could drift from canonical runtime behavior if it duplicates too much logic instead of reusing helpers.

### Current evidence-bearing artifacts
- `workspace/reports/identity_validation.json`
- `workspace/reports/full_dataset_validation.json`
- `workspace/final/dataset_manifest.json`
- current notebook/config/runtime rehab state from session `rehab-20260308-01`

### Most trustworthy files
- `requirements.txt`
- `constraints.txt`
- `configs/train_sft.yaml`
- `configs/train_dpo.yaml`
- `notebooks/40_train_sft_unsloth_qwen35_4b.ipynb`
- `notebooks/50_train_dpo_unsloth_qwen35_4b.ipynb`
- `lumis1/export_smoke.py`

### Least trustworthy / stale files
- archive-only GGUF/export metadata and scripts
- any operator assumption that notebook 60 already performs export

### What changed in understanding during this session
- The single-notebook Colab request is feasible, but it requires an active export layer and runtime overrides, not just notebook concatenation.
- The safest export path is via Unsloth’s documented GGUF API, with repo pins first and auto-install fallback only when environment sanity fails.

### Artifacts produced this session
- Planning state only so far.

### Most recent validation status
- Repo rehab validation from session `rehab-20260308-01` remains the current baseline.

### Last known good commands
```bash
# python -m pytest -q
# python scripts/validate_identity_pack.py --strict
# python scripts/validate_full_dataset.py --allow-small-sample --strict
# python scripts/render_dataset_manifest.py --allow-small-sample
```

### Exact next step for the next agent
- Add a tested helper for Colab run planning/runtime overrides, then implement a single Colab-first orchestration notebook with active GGUF export and artifact download support.

## Snapshot 2026-03-08 09:36:51 +02:00 — Session rehab-20260308-03

### Canonical execution path
- `configs/*.yaml`
- `notebooks/00_env_sanity_and_pinning.ipynb`
- `notebooks/10_validate_identity_pack.ipynb`
- `notebooks/20_build_open_dataset_mix.ipynb`
- `notebooks/30_merge_and_validate_full_dataset.ipynb`
- `notebooks/40_train_sft_unsloth_qwen35_4b.ipynb`
- `notebooks/50_train_dpo_unsloth_qwen35_4b.ipynb`
- `notebooks/60_eval_export_smoke.ipynb`
- `notebooks/90_colab_main_pipeline.ipynb` as the sequential Colab convenience surface
- `lumis1/*`

### Proven claims
- The repo now contains a single sequential Colab notebook that compiles and is regression-tested.
- Notebook 90 uses the repo-pinned Unsloth baseline by default and documents the auto-installer as fallback only.
- Notebook 90 derives per-run SFT, DPO, export, and eval paths from a pipeline prefix instead of forcing manual config edits.
- Notebook 90 requires a user-supplied identity folder containing `sft_dataset.jsonl` and `preference_dataset.jsonl`.

### Unproven claims
- Any real end-to-end Colab completion on the requested GA6 runtime.
- Any completed SFT, DPO, eval, or GGUF export run from notebook 90.
- Any proof that direct Unsloth GGUF export succeeds on the final DPO artifact in this exact Colab environment.

### Current blockers
- The new Colab orchestration path still needs a real execution to move from static readiness to proof-bearing operation.
- GGUF smoke remains partial unless parity pairs or another GGUF inference check are provided.

### Active defects
- No new code-level defects were found in the notebook generation or compile/test surface.
- Remaining risk is runtime proof, not static integrity.

### Current risk register
- Colab environment drift can still force the fallback installer path.
- A failed direct GGUF export could still leave only merged 16-bit recovery artifacts.
- Operators may overread the presence of notebook 90 as execution proof unless they inspect `workspace/runs/<run_id>/`.

### Current evidence-bearing artifacts
- `workspace/reports/identity_validation.json`
- `workspace/reports/full_dataset_validation.json`
- `workspace/final/dataset_manifest.json`
- `notebooks/90_colab_main_pipeline.ipynb`
- `tests/test_colab_main_notebook.py`

### Most trustworthy files
- `scripts/build_colab_main_notebook.py`
- `notebooks/90_colab_main_pipeline.ipynb`
- `requirements.txt`
- `constraints.txt`
- `lumis1/run_evidence.py`
- `lumis1/export_smoke.py`
- `PROJECT_BRIEF.md`
- `STATE.yaml`

### Least trustworthy / stale files
- any future notebook 90 execution evidence that lacks populated `checksums/`, `reports/`, or `STATUS.json`
- archive-only export notes under `archive/`
- any assumption that export smoke currently proves runnable GGUF inference parity

### What changed in understanding during this session
- The single-notebook Colab request is workable without changing the canonical modular notebook chain.
- The cleanest maintainable surface is a generated notebook, not hand-maintained JSON.
- GGUF-first export can be encoded directly in the convenience notebook while keeping proof claims conservative.

### Artifacts produced this session
- `scripts/build_colab_main_notebook.py`
- `notebooks/90_colab_main_pipeline.ipynb`
- updated `tests/test_colab_main_notebook.py`

### Most recent validation status
- `python -m pytest -q` passed with `36 passed`.
- `python -m pytest tests/test_colab_main_notebook.py -q` passed.
- all notebook JSON/code-cell compile checks passed across 8 notebooks.

### Last known good commands
```bash
# python scripts/build_colab_main_notebook.py
# python -m py_compile scripts/build_colab_main_notebook.py
# python -m pytest -q
```

### Exact next step for the next agent
- Run `notebooks/90_colab_main_pipeline.ipynb` on Colab with a real identity folder and Drive-backed workspace, then inspect `workspace/runs/<run_id>/artifacts/gguf/`, `workspace/runs/<run_id>/STATUS.json`, and the copied export bundle before making any claim that the Colab one-notebook path is fully proven.

## Snapshot 2026-03-08 09:52:06 +02:00 — Session rehab-20260308-04

### Canonical execution path
- `configs/*.yaml`
- `notebooks/00_env_sanity_and_pinning.ipynb`
- `notebooks/10_validate_identity_pack.ipynb`
- `notebooks/20_build_open_dataset_mix.ipynb`
- `notebooks/30_merge_and_validate_full_dataset.ipynb`
- `notebooks/40_train_sft_unsloth_qwen35_4b.ipynb`
- `notebooks/50_train_dpo_unsloth_qwen35_4b.ipynb`
- `notebooks/60_eval_export_smoke.ipynb`
- `notebooks/90_colab_main_pipeline.ipynb` as the sequential Colab convenience surface
- `lumis1/*`

### Proven claims
- Notebook 90 now enforces explicit tokenizer chat-template probes for Qwen3.5 non-thinking mode.
- Notebook 90 now checks repo-pinned Colab dependency drift instead of only checking for missing imports.
- Notebook 90 compile checks and regression tests pass after the hardening changes.
- The merged dataset currently contains multimodal rows, and the notebook now refuses the unverified multimodal SFT path by default.

### Unproven claims
- A proof-bearing end-to-end Colab run on the GA6 runtime.
- A verified FastVisionModel-based multimodal Qwen3.5 SFT path in this repo.
- Completed SFT, DPO, eval, or GGUF export evidence under `workspace/runs/<run_id>/`.

### Current blockers
- The all-in-one notebook is safer, but it is not yet a fully proven multimodal training surface.
- The repo still needs either a verified FastVisionModel path or a formally text-only training scope for the Colab notebook.

### Active defects
- No static notebook/code/test defect is currently open from this hardening pass.
- The remaining defect is an execution-scope gap: multimodal Qwen3.5 SFT is not yet evidence-backed.

### Current risk register
- The operator may assume the all-in-one notebook is fully multimodal-ready because the base model is vision-language capable; current repo evidence does not prove that yet.
- GGUF export may still depend on loader compatibility for local Qwen3.5 adapters even after the loader fallback improvements.
- Browser download of large GGUF files remains optional because Drive copy-out is operationally safer.

### Current evidence-bearing artifacts
- `workspace/reports/identity_validation.json`
- `workspace/reports/full_dataset_validation.json`
- `notebooks/90_colab_main_pipeline.ipynb`
- `tests/test_colab_main_notebook.py`

### Most trustworthy files
- `notebooks/90_colab_main_pipeline.ipynb`
- `tests/test_colab_main_notebook.py`
- `lumis1/main_pipeline.py`
- `PROJECT_BRIEF.md`
- `STATE.yaml`

### Least trustworthy / stale files
- any assumption that notebook 90 is already a proof-bearing multimodal Colab trainer
- any future rerun of `scripts/build_colab_main_notebook.py` that is treated as source generation rather than notebook normalization

### What changed in understanding during this session
- Qwen3.5 non-thinking mode needed explicit tokenizer-level enforcement, not just config policy wording.
- The real hidden blocker is multimodal SFT proof, not package installation alone.
- “Foolproof” in the current repo means guarding the unverified multimodal path, not quietly running it.

### Artifacts produced this session
- hardened `notebooks/90_colab_main_pipeline.ipynb`
- updated `tests/test_colab_main_notebook.py`
- safer `scripts/build_colab_main_notebook.py`

### Most recent validation status
- `python -m pytest -q` passed with `36 passed`.
- notebook 90 compile validation passed.
- all notebook JSON/code-cell compile validation passed across 8 notebooks.

### Last known good commands
```bash
# python -m pytest -q
# python scripts/build_colab_main_notebook.py
```

### Exact next step for the next agent
- Decide whether to implement and verify an explicit FastVisionModel multimodal SFT path for Qwen3.5, or intentionally narrow the all-in-one notebook to a text-only verified scope before presenting it as foolproof.

## Snapshot 2026-03-08 10:15:01 +02:00 — Session rehab-20260308-05

### Canonical execution path
- `configs/*.yaml`
- `notebooks/00_env_sanity_and_pinning.ipynb`
- `notebooks/10_validate_identity_pack.ipynb`
- `notebooks/20_build_open_dataset_mix.ipynb`
- `notebooks/30_merge_and_validate_full_dataset.ipynb`
- `notebooks/40_train_sft_unsloth_qwen35_4b.ipynb`
- `notebooks/50_train_dpo_unsloth_qwen35_4b.ipynb`
- `notebooks/60_eval_export_smoke.ipynb`
- `notebooks/90_colab_main_pipeline.ipynb`
- `lumis1/*`

### Proven claims
- The DPO notebook surfaces now handle preference rows with either `prompt` or `prompt_messages`.
- Notebook 30 and notebook 90 now normalize identity preference rows before writing `workspace/final/full_preferences.jsonl`.
- The Colab bootstrap now accepts canonical identity filenames and documented aliases.
- The Colab bootstrap no longer hardcodes the temporary rehab branch; it defaults to `main` and allows env overrides.
- `lumis1.main_pipeline` and notebook 90 now agree that GGUF artifacts live under the dedicated `*-export` run.
- `python -m pytest -q` passed with `41 passed`.
- all 8 notebooks compile after the current edits.

### Unproven claims
- A proof-bearing end-to-end Colab run on the GA6 runtime.
- A verified FastVisionModel-based multimodal Qwen3.5 SFT path in this repo.
- Completed SFT, DPO, eval, or GGUF export evidence under `workspace/runs/<run_id>/`.

### Current blockers
- The repo still lacks an evidence-backed multimodal SFT implementation for the actual merged dataset.
- The single Colab notebook remains operationally incomplete for the current multimodal full dataset unless the operator bypasses the safety guard.

### Active defects
- No static contract drift remains in the repaired DPO/bootstrap/export-layout surfaces.
- The remaining active defect is the same execution-scope gap: multimodal Qwen3.5 SFT is not yet proof-bearing.

### Current risk register
- Users may still infer that notebook 90 is end-to-end runnable because it is a single notebook; that is only true for the text-only verified path today.
- Export success still depends on real Colab runtime compatibility for the saved adapters/checkpoints.
- The local git state remains non-authoritative here; do not assume this workspace can push without proper remote state.

### Current evidence-bearing artifacts
- `workspace/reports/identity_validation.json`
- `workspace/reports/full_dataset_validation.json`
- `notebooks/90_colab_main_pipeline.ipynb`
- `tests/test_colab_main_notebook.py`
- `tests/test_main_pipeline.py`
- `tests/test_schema.py`

### Most trustworthy files
- `notebooks/90_colab_main_pipeline.ipynb`
- `notebooks/30_merge_and_validate_full_dataset.ipynb`
- `notebooks/50_train_dpo_unsloth_qwen35_4b.ipynb`
- `lumis1/main_pipeline.py`
- `lumis1/schema.py`
- `PROJECT_BRIEF.md`
- `STATE.yaml`

### Least trustworthy / stale files
- any claim that notebook 90 is already a proof-bearing multimodal trainer
- any stale remote/bootstrap instructions that mention `codex/truth-parity-rehab` as the default branch
- sample-scale artifacts under `workspace/final/` until regenerated by a real production build

### What changed in understanding during this session
- The largest immediate runtime bug was not Unsloth versioning but preference-shape drift into DPO.
- The single-notebook bootstrap had several contract mismatches that were independent of the multimodal SFT blocker.
- The repo is now more coherent, but the multimodal training gap is still the gating truth.

### Artifacts produced this session
- updated `notebooks/30_merge_and_validate_full_dataset.ipynb`
- updated `notebooks/50_train_dpo_unsloth_qwen35_4b.ipynb`
- updated `notebooks/90_colab_main_pipeline.ipynb`
- updated `lumis1/main_pipeline.py`
- updated `lumis1/schema.py`
- updated regression tests

### Most recent validation status
- `python -m pytest -q` passed with `41 passed`.
- notebook 90 compiles.
- all notebook JSON/code-cell compile checks passed across 8 notebooks.
- `python scripts/build_colab_main_notebook.py` completed successfully.

### Last known good commands
```bash
# python -m pytest -q
# python scripts/build_colab_main_notebook.py
```

### Exact next step for the next agent
- Build the explicit FastVisionModel multimodal SFT path and verify it on Colab, or intentionally narrow notebook 90 to a text-only training scope everywhere it is described before any push that markets it as the main end-to-end notebook.

## 2026-03-08T10:32:00+02:00 | notebook-path-correction

### Canonical execution path as currently understood
- `configs/*.yaml`
- `notebooks/00 -> 10 -> 20 -> 30 -> 40 -> 50 -> 60`
- `notebooks/90_colab_main_pipeline.ipynb` as the single Colab convenience surface over the same stages
- `lumis1/*`
- `workspace/reports/*`

### Proven claims
- `notebooks/90_colab_main_pipeline.ipynb` exists on `main`.
- The confusion came from an uncommitted instruction-doc detour, not from notebook 90 being absent.
- `main` already contains today’s rehab work at commit `4c4fcfa`.

### Unproven claims
- A proof-bearing full Colab run of notebook 90.
- A proof-bearing multimodal SFT path for the current mixed dataset.

### Current blockers
- The remaining real blocker is still the unverified multimodal Qwen3.5 SFT path.
- A stale remote branch still exists until explicitly deleted.

### Active defects
- No new code defect was found in notebook 90 during this correction block.
- The active operator defect was documentation drift caused by an uncommitted wrong document.

### Current risk register
- Users can still over-read notebook 90 as fully end-to-end if they ignore the current multimodal limitation.
- Remote branch clutter can create confusion about which branch is authoritative.

### Current evidence-bearing artifacts
- `notebooks/90_colab_main_pipeline.ipynb`
- `NOTEBOOK_OPERATOR_INSTRUCTIONS.md`
- `PROJECT_BRIEF.md`
- `STATE.yaml`

### Most trustworthy files
- `notebooks/90_colab_main_pipeline.ipynb`
- `NOTEBOOK_OPERATOR_INSTRUCTIONS.md`
- `OPERATOR_RUN_ORDER.md`

### Least trustworthy or stale files
- Any leftover admin/relink instructions not committed as part of the canonical operator path
- Any remote non-`main` rehab branch that survived cleanup

### What changed in understanding during this session
- The unified notebook was not lost or overwritten in git; the confusion was caused by my later local uncommitted edits.

### What the next agent should do without rereading everything
- Delete the stale remote rehab branch, commit the notebook-instruction correction to `main`, push `main`, and only then continue work on the multimodal SFT gap.

## 2026-03-08T10:37:00+02:00 | notebook-wording-fix

### Canonical execution path as currently understood
- `notebooks/90_colab_main_pipeline.ipynb` exists on `main` and defaults to bootstrapping `main`

### Proven claims
- The unified notebook is present and committed.
- The last contradictory wording about a rehab branch has been removed locally.

### Unproven claims
- End-to-end Colab proof remains unproven.

### Current blockers
- The real blocker remains the multimodal SFT gap, not notebook discoverability.

### Active defects
- The notebook-path discoverability issue is addressed by the new instruction document plus corrected notebook wording.

### What changed in understanding during this session
- Part of the perceived breakage was wording drift inside notebook 90, not missing code.

### What the next agent should do without rereading everything
- Push the notebook wording fix to `main`, then continue only with substantive runtime work.
