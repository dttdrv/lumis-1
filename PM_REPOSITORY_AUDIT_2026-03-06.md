# Lumis-1 Repository Audit Report

Date: 2026-03-06
Prepared for: Project management review
Workspace audited: `C:\Users\deyan\Projects\Lumis-1`

## 1. Executive summary

This repository is not a completed training project. It is a mixed workspace containing:

- one completed local identity-dataset generation run dated 2026-03-03;
- one local-only scaffold rebuild and cleanup pass dated 2026-03-04;
- one current PM audit and verification pass dated 2026-03-06;
- a very large amount of archived legacy material preserved inside the same tree.

The most important management conclusion is this:

- The canonical identity pack is real and internally consistent.
- The active notebooks/configs support a guarded local dry-run scaffold and manual RunPod handoff.
- The current output layer only proves dry-run/sample dataset work, not production dataset assembly, training, evaluation, or export.
- The script layer is partially broken against the current config schema and should not be treated as the canonical execution path without repair.

## 2. Audit scope and method

I audited the repository as it exists on 2026-03-06. This was not a git-history audit because the workspace is not a live git checkout; there is no `.git` directory under the project root.

The audit covered:

- every file in the repository tree via inventory crawl;
- direct review of the active scaffold files;
- direct review of the current output layer;
- direct review of the current identity-pipeline source and canonical identity output;
- direct review of the archive and historical handoff layer;
- fresh local verification commands run during this audit.

The full per-file appendix is here:

- `workspace/reports/pm_audit_20260306_corrected/full_file_inventory.csv`
- `workspace/reports/pm_audit_20260306_corrected/inventory_summary.json`

The earlier auto-generated inventory here is not fully trustworthy because it marks every file as `active`:

- `workspace/reports/pm_audit_20260306/full_file_inventory.csv`
- `workspace/reports/pm_audit_20260306/inventory_summary.json`

## 3. Repository shape

Fresh inventory on 2026-03-06 counted `3816` files.

Status breakdown:

- `51` active scaffold files
- `21` current identity-pipeline source/support files
- `19` canonical identity output files
- `26` current output/report files
- `3661` archived historical files
- `37` cache files
- `1` uncategorized current miscellaneous file

This means almost the entire tree is historical or generated material. The active hand-maintained scaffold is comparatively small.

## 4. High-confidence chronology

### 2026-03-03: identity dataset generation completed locally

This is proven by the canonical identity output folder:

- `Dataset/identity_dataset/output/full_run_codex_spark_xhigh/run_manifest.json`
- `Dataset/identity_dataset/output/full_run_codex_spark_xhigh/state.json`
- `Dataset/identity_dataset/output/full_run_codex_spark_xhigh/review_report.json`
- `Dataset/identity_dataset/output/full_run_codex_spark_xhigh/review_logs/*`
- `Dataset/identity_dataset/output/full_run_codex_spark_xhigh/sft_dataset.jsonl`
- `Dataset/identity_dataset/output/full_run_codex_spark_xhigh/preference_dataset.jsonl`

These files consistently report:

- `run_id = identity-20260303T162023Z`
- `status = completed` or finalized equivalent
- `100000` SFT rows
- `25000` preference pairs
- zero accepted invalid final rows in the review logs

### 2026-03-04: cleanup and scaffold rebuild

This is proven by:

- `archive/README.md`
- `archive/20260304_222305/CLEANUP_PLAN.md`
- `archive/20260304_222305/CLEANUP_LOG.md`
- `archive/20260304_222305/FINAL_SUMMARY.md`
- `LOG.md`

This phase archived stale/generated material, kept the canonical identity pack in place, and rebuilt the repo around a local-only scaffold and manual RunPod execution story.

### 2026-03-06: PM audit and verification

This is proven by:

- `workspace/reports/verification_20260306/active_generation_audit_fresh.json`
- `workspace/reports/verification_20260306/trivy_fs_high_critical.json`
- `workspace/reports/pm_audit_20260306_corrected/*`
- this report file

## 5. Fresh verification reproduced during this audit

### Passed

1. Unit tests:
   - Command: `python -m pytest tests/test_schema.py tests/test_mixing_math.py tests/test_cot_scrub.py -q`
   - Result: `16 passed`

2. Config YAML parsing:
   - All files under `configs/*.yaml` parsed successfully.

3. Notebook structural validation:
   - All `notebooks/*.ipynb` parsed as JSON successfully.
   - All notebook code cells compiled successfully as Python source.

4. Active generation-path hygiene audit:
   - Command: `python scripts/audit_active_generation_paths.py --output workspace/reports/verification_20260306/active_generation_audit_fresh.json`
   - Result: `ACTIVE_PIPELINE_NO_GENERATION_PATHS_FOUND`
   - Meaning: active code paths had zero forbidden-provider violation hits under this audit's heuristic scan.

5. CLI Trivy filesystem scan:
   - Command used a HIGH/CRITICAL filesystem scan across the repo.
   - Result: `63` HIGH/CRITICAL findings total.
   - Important qualifier: all `63` findings were in archived legacy material under `archive/legacy_generated/...`; `0` were in current active/current-output/current-identity paths.

### Failed

Two repository validator scripts no longer match the active config schema:

1. `scripts/validate_identity_pack.py`
   - Failure: `KeyError: 'identity'`
   - Cause: script expects older config keys not present in current `configs/dataset_mixture.yaml`

2. `scripts/validate_full_dataset.py`
   - Failure: `KeyError: 'bucket_targets'`
   - Cause: same problem; script expects an older config structure

This is a real defect, not a tooling fluke. It means the active script layer drifted away from the active config layer.

## 6. What is actually complete

### A. Canonical identity dataset generation

This is the strongest completed work in the repo.

Evidence:

- `Dataset/identity_dataset/output/full_run_codex_spark_xhigh/run_manifest.json`
- `Dataset/identity_dataset/output/full_run_codex_spark_xhigh/state.json`
- `Dataset/identity_dataset/output/full_run_codex_spark_xhigh/review_report.json`
- `Dataset/identity_dataset/output/full_run_codex_spark_xhigh/quality_review_report.md`
- `Dataset/identity_dataset/output/full_run_codex_spark_xhigh/full_internal_dataset_report_eptesicus_lumis1.pdf`

What worked:

- local chunked generation completed;
- review/finalization completed;
- row counts reached target;
- dedupe ledger was produced;
- category/language/modality manifests were produced;
- spot-check and stress-test packs were produced.

What remains unproven:

- real downstream training quality;
- real multimodal grounding quality on external image corpora;
- use of a live external teacher model during generation.

### B. Local-only scaffold rebuild

This is the second strongest completed work.

Evidence:

- `PROJECT_BRIEF.md`
- `LOG.md`
- `archive/README.md`
- `DETAILED_LOCAL_BUILD_REPORT.md`
- `notebooks/*.ipynb`
- `configs/*.yaml`

What worked:

- repo was re-centered on notebooks, configs, validators, and operator docs;
- active-path generation/provider references were fenced away from current code;
- workspace output folders were created;
- tests and notebook/config structural checks were made possible.

What remains unproven:

- that scripts, notebooks, docs, and configs are fully synchronized;
- that manual RunPod instructions have been executed end to end.

### C. Notebook-driven dry-run/sample outputs

Current output layer proves a dry-run/sample flow succeeded.

Evidence:

- `workspace/interim/open_sft.jsonl`
- `workspace/interim/open_preferences.jsonl`
- `workspace/final/full_sft.jsonl`
- `workspace/final/full_preferences.jsonl`
- `workspace/reports/open_corpus_build_report.json`
- `workspace/reports/merge_full_warehouse_report.json`
- `workspace/reports/full_dataset_validation.json`

What worked:

- synthetic open-corpus generation;
- sample-scale merge/finalization;
- sample-scale final validation;
- manifest writing.

What remains unproven:

- real HF ingestion at scale;
- production-size full dataset assembly;
- training/eval/export completion.

## 7. What did not work, or is currently unreliable

### A. Script/config drift

This is the highest-confidence defect discovered in the current active scaffold.

Broken or stale assumptions include:

- `scripts/validate_identity_pack.py` expects `cfg["identity"]`
- `scripts/validate_full_dataset.py` expects `cfg["bucket_targets"]`
- `scripts/build_open_corpus.py` expects older keys such as `identity`, `global_targets`, and `bucket_targets`
- `scripts/merge_full_warehouse.py` expects older keys such as `identity`, `global_targets`, `bucket_targets`, and `dpo_sources`
- `scripts/render_dataset_manifest.py` expects older keys such as `identity`, `bucket_targets`, and `global_targets`
- `scripts/resume_train_local.sh` still points to archived config filenames:
  - `configs/train_sft_qwen35_4b_unsloth.yaml`
  - `configs/train_dpo_qwen35_4b_unsloth.yaml`

Management interpretation:

- Current notebooks/configs are the practical execution path.
- Current scripts are partially obsolete and should not be advertised as production-ready automation.

### B. Documentation drift

Several docs overstate the strictness or completeness of current notebook behavior.

Confirmed examples:

- `STATE.yaml` said verification was pending even though tests and parsing checks had already been run.
- `DATASET_MANIFEST_SPEC.md` expects keys the actual manifest does not write.
- `INPUT_CONTRACT_IDENTITY.md` and parts of `DETAILED_LOCAL_BUILD_REPORT.md` imply stricter identity-filename enforcement than the current config/notebook fallback logic actually uses.
- `DETAILED_LOCAL_BUILD_REPORT.md` is behind the active configs on source inventory details.

### C. Output layer is sample-scale, not production

Current output counts:

- `workspace/interim/open_sft.jsonl`: `5000` rows
- `workspace/interim/open_preferences.jsonl`: `5000` rows
- `workspace/final/full_sft.jsonl`: `6250` rows
- `workspace/final/full_preferences.jsonl`: `2181` rows

These are dry-run/sample artifacts, not evidence of a completed warehouse.

### D. No training, evaluation, or export evidence

There is no active evidence under `workspace/runs/` of:

- SFT completion
- DPO completion
- evaluation completion
- export completion

The repo documents those steps, but does not prove they happened.

## 8. File-by-file analysis of the active scaffold

### Root and operator documents

- `PROJECT_BRIEF.md`: accurate high-level charter; descriptive, not evidentiary.
- `STATE.yaml`: useful state file, but previously stale and behind actual verification.
- `LOG.md`: credible rebuild log; narrative only, with no embedded command evidence.
- `DETAILED_LOCAL_BUILD_REPORT.md`: broad existing summary; valuable, but partly out of sync with configs and notebooks.
- `DATASET_MANIFEST_SPEC.md`: stronger than actual implementation; currently aspirational in parts.
- `DATA_LICENSE_LEDGER.md`: useful governance document; mostly aligned with allowlist/licensing configs.
- `INPUT_CONTRACT_IDENTITY.md`: useful contract note; stricter in prose than the live config/notebook path resolution.
- `MODEL_CARD_DRAFT.md`: clearly a draft, not a release claim.
- `OPERATOR_RUN_ORDER.md`: good run order, but some checks are described more strictly than currently enforced.
- `RUNPOD_OPERATOR_CHECKLIST.md`: useful operator checklist; does not prove any remote execution.
- `.env.example`: safe environment template; no issues.
- `requirements.txt`: coherent dependency intent, but not a reproducible lock.
- `constraints.txt`: much closer to a reproducible environment story.
- `source_registry.yaml`: helpful reference ledger, but stale relative to active configs.

### Configs

- `configs/chat_template_policy.yaml`: coherent and aligned with the no-thinking/CoT-rejection posture.
- `configs/dataset_mixture.yaml`: best current source of truth for active mixture and outputs.
- `configs/dataset_sources_allowlist.yaml`: best current source of truth for enabled/disabled sources and licensing metadata.
- `configs/license_policy.yaml`: strong governance layer, but still leaves subset-review work to humans.
- `configs/paths.yaml`: useful canonical path map; explicitly allows fallback legacy identity filenames.
- `configs/run_profiles.yaml`: adequate memory profiles, but only coarse-grained.
- `configs/train_sft.yaml`: safe-by-default active SFT config.
- `configs/train_dpo.yaml`: safe-by-default active DPO config.

### Runtime code under `lumis1/`

- `lumis1/cot_scrub.py`: strongest-tested utility in the runtime layer; working and covered.
- `lumis1/export_smoke.py`: plausible helper, but untested and heuristic-heavy.
- `lumis1/filters.py`: coherent but under-tested; broad exception handling may hide real defects.
- `lumis1/hashing.py`: simple deterministic helper; untested but straightforward.
- `lumis1/hf_ingest.py`: plausible ingestion boundary; untested and potentially memory-heavy.
- `lumis1/license_ledger.py`: narrow governance helper; indirectly validated through schema tests.
- `lumis1/mixing_math.py`: strong pure-function module with passing tests.
- `lumis1/schema.py`: central validator; text/private-local path covered, preference and multimodal path coverage weaker.
- `lumis1/vision_schema.py`: strict multimodal validator; high-value, but currently untested in-repo.

### Tests

- `tests/test_cot_scrub.py`: passed; covers the main CoT marker and thinking-off behavior.
- `tests/test_mixing_math.py`: passed; good deterministic math coverage.
- `tests/test_schema.py`: passed; useful integration-style coverage, but does not fully cover multimodal or preference-row paths.

### Scripts

- `scripts/common_dataset.py`: current shared helper layer and mostly coherent.
- `scripts/audit_active_generation_paths.py`: working and useful; one of the few script-layer files clearly confirmed to work today.
- `scripts/build_open_corpus.py`: stale against current config schema and not representative of the current notebook dry-run path.
- `scripts/merge_full_warehouse.py`: stale against current config schema.
- `scripts/render_dataset_manifest.py`: stale against current config schema.
- `scripts/validate_identity_pack.py`: broken today against current config schema.
- `scripts/validate_full_dataset.py`: broken today against current config schema.
- `scripts/launch_train_local.sh`: chains the stale validators/builders, so it should be treated as unreliable.
- `scripts/resume_train_local.sh`: still points to archived config filenames.
- `scripts/export_artifacts.sh`: minimal wrapper; not broken by itself, but not a real export pipeline.

### Notebooks

- `notebooks/00_env_sanity_and_pinning.ipynb`: validates environment, but also mutates it.
- `notebooks/10_validate_identity_pack.ipynb`: solid count/CoT checks; only samples schema rows.
- `notebooks/20_build_open_dataset_mix.ipynb`: appears to be the real source of current synthetic dry-run outputs.
- `notebooks/30_merge_and_validate_full_dataset.ipynb`: appears to be the real source of current dry-run final outputs.
- `notebooks/40_train_sft_unsloth_qwen35_4b.ipynb`: safe-by-default scaffold, not execution proof.
- `notebooks/50_train_dpo_unsloth_qwen35_4b.ipynb`: safe-by-default scaffold, not execution proof; implementation path is more generic Transformers/TRL than the label suggests.
- `notebooks/60_eval_export_smoke.ipynb`: guarded end-stage notebook; does not prove real export/eval completion.

## 9. Current output layer

### Interim outputs

- `workspace/interim/open_sft.jsonl`: sample/dry-run open-corpus SFT records; structurally valid but synthetic.
- `workspace/interim/open_preferences.jsonl`: sample/dry-run preference records; structurally valid but synthetic.

### Final outputs

- `workspace/final/full_sft.jsonl`: sample/dry-run merged final SFT dataset.
- `workspace/final/full_preferences.jsonl`: sample/dry-run merged final preference dataset.
- `workspace/final/full_dataset_manifest.json`: compact machine manifest for the sample output.
- `workspace/final/dataset_manifest.json`: richer manifest snapshot for the sample output.
- `workspace/final/dataset_manifest.md`: human-readable summary of the same sample output.

### Active report files

- `workspace/reports/identity_validation.json`: strongest current output-layer evidence because it validates the real canonical identity pack.
- `workspace/reports/open_corpus_build_report.json`: explicitly a synthetic dry-run report.
- `workspace/reports/merge_full_warehouse_report.json`: explicitly a dry-run/sample merge report.
- `workspace/reports/full_dataset_validation.json`: validates the sample final dataset, not a production one.
- `workspace/reports/active_generation_audit*.json` and `.txt`: useful hygiene audits; active surface is clean under the implemented heuristic.
- `workspace/reports/pattern_hits_full.json` and `pattern_hits_paths.json`: useful but noisy; archive-heavy.
- `workspace/reports/trivy_scan_workspace*.json`: weak result stubs with zero listed findings; much less informative than the fresh CLI scan file.
- `workspace/reports/verification_20260306/active_generation_audit_fresh.json`: fresh audit rerun.
- `workspace/reports/verification_20260306/trivy_fs_high_critical.json`: fresh and meaningful scan result, showing findings are archive-only.

## 10. Identity pipeline source and canonical identity output

### Source/support files under `Dataset/identity_dataset/`

- `__init__.py`: package marker only.
- `chunked_generation_runbook.md`: useful operational guide for the identity-generation pipeline.
- `codex_chunk_worker.py`: worker implementation for chunk generation/review.
- `config/identity_dataset_config.json`: main config for the identity run.
- `config/identity_dataset_config_full_run_nodedupe.json`: alternate config that weakens dedupe; non-canonical.
- `identity_dataset_builder.py`: main builder library.
- `identity_policy_sheet.md`: governing identity prompt/policy sheet.
- `prompt_codex_spark_xhigh_all_samples.txt`: top-level generation prompt.
- `prompt_codex_spark_xhigh_finalize.txt`: finalization prompt.
- `prompt_codex_spark_xhigh_subagent_generator.txt`: generator subagent prompt.
- `prompt_codex_spark_xhigh_subagent_reviewer.txt`: reviewer subagent prompt.
- `README.md`: explicitly frames the identity generator as offline/reproducible by default.
- `run_codex_spark_xhigh_supervisor.py`: supervisor/orchestrator for the canonical run.
- `write_manual_samples.py`: fallback/manual generator.
- `identity_dataset/`: empty placeholder directory.

### Canonical completed run under `Dataset/identity_dataset/output/full_run_codex_spark_xhigh/`

- `run_manifest.json`: primary completion proof.
- `state.json`: finalized supervisor state proof.
- `heartbeat.log`: execution trace; one late fatal-looking line is explicitly treated as non-blocking by the quality report.
- `sft_dataset.jsonl`: `100000` rows.
- `preference_dataset.jsonl`: `25000` rows.
- `category_manifest.json`: near-target category distribution.
- `language_manifest.json`: broad multilingual coverage.
- `multimodal_manifest.json`: `9515` multimodal rows and `90485` text-only rows.
- `review_report.json`: aggregated review summary.
- `review_logs/review_final_sft.json`: final SFT review accepted.
- `review_logs/review_final_pref.json`: final preference review accepted.
- `review_logs/review_final_report.json`: final report accepted.
- `quality_review_report.md`: strongest human-readable quality summary.
- `full_internal_dataset_report_eptesicus_lumis1.pdf`: binary corroboration of the same run.
- `dedupe_exact.sha256.txt`: exact-dedupe evidence ledger.
- `spot_checks.jsonl`: audit sample set.
- `stress_test_pack.jsonl`: adversarial/manual inspection sample set.
- `identity_policy_sheet.md`: policy copy frozen into the output folder.
- `how_dataset_could_still_fail.md`: candid remaining-risk note.
- `chunks/pending/` and `chunks/reviewed/`: empty now, suggesting cleanup of temporary shard artifacts after finalization.

Management interpretation:

- This canonical identity run is real and internally consistent.
- It is the single strongest piece of completed substantive work in the repository.

## 11. Historical and archived material

### `archive/README.md`

This file is authoritative about the 2026-03-04 archival action. It clearly states that stale generated artifacts were moved for cleanliness while the identity dataset directory was left in place.

### `archive/20260304_222305/*`

These files collectively prove a cleanup/rebuild effort happened and that the project considered itself ready for manual RunPod execution next. They do not prove that RunPod execution actually happened.

Direct files in that folder:

- `00_repo_audit_and_cleanup.ipynb`
- `CLEANUP_LOG.md`
- `CLEANUP_PLAN.md`
- `CONTEXT_HANDOVER.md`
- `DATASET_ALLOWLIST_AND_LICENSE_NOTES.md`
- `eval_gates.yaml`
- `FINAL_SUMMARY.md`
- `LOCAL_DRY_RUN_REPORT.md`
- `MANUAL_RUNPOD_HANDOFF.md`
- `README_CURRENT_STATE.md`
- `REPO_INVENTORY.md`
- `REQUIRED_INPUTS.md`
- `RUNPOD_NEXT_STEPS_DETAILED_REPORT.md`
- `SOURCE_REGISTRY.md`
- `train_dpo_qwen35_4b_unsloth.yaml`
- `train_sft_qwen35_4b_unsloth.yaml`
- `WHAT_STILL_CAN_FAIL.md`

All are historical, useful, and superseded by the active scaffold.

### `archive/legacy_generated/pre_2026_03_04_rebuild/*`

This is the dominant mass of the repository.

Meaningful families inside it:

- archived prior identity-run outputs;
- archived legacy pipeline/planning stacks;
- archived internal status reports;
- archived third-party/reference source material under `Dataset/output/oss_refs/*`.

These files matter for auditability, but they are not part of the active execution path.

They are also the source of:

- all current HIGH/CRITICAL Trivy findings found during this audit;
- nearly all provider-pattern hits in the generation-path audits.

## 12. External/factual checks used during the audit

I verified one external claim area against current official docs:

- Trivy official guidance confirms filesystem scans can cover vulnerabilities, misconfigurations, secrets, and licenses, and that HIGH/CRITICAL filtering is a normal severity filter for such repo audits.
- Unsloth official docs confirm the general project direction is plausible: Unsloth documents Qwen fine-tuning and also a distinct vision model path.

These checks support the audit interpretation, but they do not change the repo-internal conclusions above.

## 13. PM-ready bottom line

If you need one paragraph for management, use this:

Lumis-1 currently contains one real completed local identity-dataset generation run and one later local-only scaffold rebuild for manual RunPod execution. The active notebooks, configs, tests, and current output files support a claim of guarded local dry-run readiness, not a claim of production dataset completion or finished training/eval/export. The largest current technical issue is drift between the active script layer and the active config/notebook layer: several scripts now fail against the current config schema, while the notebooks and configs remain the more credible active path. The archive is very large and preserved for traceability, but it also contains all current HIGH/CRITICAL Trivy findings and most legacy provider-call references.

## 14. Action items

1. Decide whether notebooks or scripts are the canonical execution path. Right now they are not aligned.
2. Repair or retire the stale scripts:
   - `scripts/validate_identity_pack.py`
   - `scripts/validate_full_dataset.py`
   - `scripts/build_open_corpus.py`
   - `scripts/merge_full_warehouse.py`
   - `scripts/render_dataset_manifest.py`
   - `scripts/resume_train_local.sh`
3. Reconcile docs against actual implementation:
   - `STATE.yaml`
   - `DATASET_MANIFEST_SPEC.md`
   - `INPUT_CONTRACT_IDENTITY.md`
   - `DETAILED_LOCAL_BUILD_REPORT.md`
4. Keep using the canonical identity pack as the strongest completed artifact.
5. Do not claim training, evaluation, or export completion until `workspace/runs/` and corresponding reports contain real outputs.
6. Consider moving or separately storing the archive if scan noise and false escalation against historical material becomes a management problem.

## 15. Appendix

Every file in the repository has a row in:

- `workspace/reports/pm_audit_20260306_corrected/full_file_inventory.csv`

The corrected inventory summary is here:

- `workspace/reports/pm_audit_20260306_corrected/inventory_summary.json`

