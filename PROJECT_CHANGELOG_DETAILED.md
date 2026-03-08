# PROJECT_CHANGELOG_DETAILED

## Entry 2026-03-08 08:00:56 +02:00 — Session rehab-20260308-01

### Objective
- Bootstrap repository memory and begin the Lumis-1 truth-and-parity rehabilitation pass.

### Repository areas inspected
- Root state and operator docs
- `configs/*.yaml`
- `lumis1/*`
- `scripts/*`
- `notebooks/00/10/30/50/60`
- `Dataset/identity_dataset/*`
- `workspace/reports/*`
- `workspace/final/*`
- `workspace/runs/*`

### Files modified
- `PROJECT_CHANGELOG_DETAILED.md`
- `PROJECT_TIME_CAPSULE.md`

### Commands executed
```bash
# Get-ChildItem -Force
# Get-Content PROJECT_BRIEF.md, STATE.yaml, LOG.md, DETAILED_LOCAL_BUILD_REPORT.md, DATASET_MANIFEST_SPEC.md, INPUT_CONTRACT_IDENTITY.md, OPERATOR_RUN_ORDER.md, RUNPOD_OPERATOR_CHECKLIST.md
# Get-Content configs/*.yaml
# Get-Content lumis1/*.py
# Get-Content scripts/*.py
# Get-Content tests/*.py
# python notebook-cell extraction helpers
# Get-Content Dataset/identity_dataset/... and workspace/reports/identity_validation.json
# rg drift and notebook/script references
# Context7 query for TRL DPOTrainer wording
```

### Outputs / reports produced
- Initial repository memory bootstrap files.

### Bugs / errors observed
- Workspace is not a live git checkout.
- `scripts/validate_identity_pack.py` is stale against current config schema.
- `scripts/validate_full_dataset.py` is stale against current config schema.
- `scripts/render_dataset_manifest.py` emits a stale manifest shape.
- `scripts/build_open_corpus.py` and `scripts/merge_full_warehouse.py` reflect a legacy pipeline model.

### Assumptions made
- The canonical identity run remains read-only and authoritative.
- The notebook/config/runtime surface is the current canonical execution path.
- Current `workspace/interim/*` and `workspace/final/*` outputs are sample-scale only.

### Decisions made
- Use in-repo memory as the durable audit trail for this session.
- Prefer thin parity wrappers for kept scripts and explicit notebook-routing shims for retired ones.
- Use shared runtime helpers under `lumis1/` to remove notebook/script drift.

### Rationale
- The repo has no git history in this workspace.
- The strongest completed artifact is the identity run, not the current full-dataset path.
- Shared helpers are the smallest maintainable way to keep notebooks, scripts, and docs aligned.

### Risks / uncertainties introduced
- Notebook JSON edits must stay structurally valid.
- Current sample outputs use a legacy row shape, so validators need compatibility handling during transition.

### Rollback / recovery notes
- If the rehabilitation introduces regressions, revert the new shared helpers and restore scripts to explicit deprecation shims while keeping the memory files.

### Next recommended step
- Implement shared identity validation, manifest, full-dataset validation, and run-evidence helpers before touching the repaired wrappers and docs.

## Entry 2026-03-08 08:48:56 +02:00 — Session rehab-20260308-01

### Objective
- Complete the truth-and-parity rehabilitation pass by repairing active wrappers, reconciling docs/configs/notebooks with the canonical path, adding regression coverage, and introducing a proof-bearing `workspace/runs/<run_id>/` contract.

### Repository areas inspected
- `configs/*.yaml`
- `lumis1/*.py`
- `scripts/*.py`
- `notebooks/00/10/30/40/50/60`
- `tests/*`
- `workspace/reports/*`
- `workspace/final/*`
- `workspace/runs/*`

### Files modified
- `PROJECT_BRIEF.md`
- `STATE.yaml`
- `LOG.md`
- `DATASET_MANIFEST_SPEC.md`
- `INPUT_CONTRACT_IDENTITY.md`
- `DETAILED_LOCAL_BUILD_REPORT.md`
- `OPERATOR_RUN_ORDER.md`
- `RUNPOD_OPERATOR_CHECKLIST.md`
- `source_registry.yaml`
- `configs/paths.yaml`
- `configs/dataset_mixture.yaml`
- `configs/train_sft.yaml`
- `configs/train_dpo.yaml`
- `lumis1/__init__.py`
- `lumis1/identity_pack.py`
- `lumis1/full_dataset.py`
- `lumis1/run_evidence.py`
- `lumis1/vision_schema.py`
- `scripts/validate_identity_pack.py`
- `scripts/validate_full_dataset.py`
- `scripts/render_dataset_manifest.py`
- `scripts/build_open_corpus.py`
- `scripts/merge_full_warehouse.py`
- `scripts/launch_train_local.sh`
- `scripts/resume_train_local.sh`
- `scripts/export_artifacts.sh`
- `notebooks/00_env_sanity_and_pinning.ipynb`
- `notebooks/10_validate_identity_pack.ipynb`
- `notebooks/30_merge_and_validate_full_dataset.ipynb`
- `notebooks/40_train_sft_unsloth_qwen35_4b.ipynb`
- `notebooks/50_train_dpo_unsloth_qwen35_4b.ipynb`
- `notebooks/60_eval_export_smoke.ipynb`
- `pytest.ini`
- `tests/test_identity_pack.py`
- `tests/test_full_dataset_runtime.py`
- `tests/test_filters.py`
- `tests/test_vision_schema.py`
- `tests/test_export_smoke.py`
- `tests/test_run_evidence.py`
- `tests/test_script_wrappers.py`
- `workspace/reports/identity_validation.json`
- `workspace/reports/full_dataset_validation.json`
- `workspace/final/dataset_manifest.json`
- `workspace/final/dataset_manifest.md`

### Commands executed
```bash
# python notebook cell extraction helpers for notebooks 30/40/50/60
# python -m pytest -q
# python scripts/validate_identity_pack.py --strict
# python scripts/validate_full_dataset.py --allow-small-sample --strict
# python scripts/render_dataset_manifest.py --allow-small-sample
# rg drift and path references across configs/notebooks/docs
# python notebook JSON/code compile verification
# python workspace/runs STATUS.json scan
# time lookup for Europe/Sofia session timestamps
# subagent review of runtime/scripts/notebooks/docs
```

### Outputs / reports produced
- `workspace/reports/identity_validation.json` regenerated against canonical identity filenames.
- `workspace/reports/full_dataset_validation.json` regenerated in current schema with input hashes.
- `workspace/final/dataset_manifest.json` regenerated in the canonical schema.
- `workspace/final/dataset_manifest.md` regenerated from the canonical manifest renderer.
- Expanded regression suite covering identity fallback, manifest rebuild parity, run-evidence config/runtime parity, script shims, filters, vision schema, export smoke, and full-dataset runtime helpers.

### Bugs / errors observed
- Review found notebook 30 sample-mode mismatch versus validator behavior.
- Review found stale validation report reuse in `scripts/render_dataset_manifest.py`.
- Review found notebook 50/60 run-path mismatch and missing DPO/eval run-evidence parity.
- Review found notebook 60 could mark incomplete evidence as `completed`.
- Review found `DETAILED_LOCAL_BUILD_REPORT.md` still overclaimed exact legacy filenames and repo maturity.
- `lumis1/run_evidence.py` initially failed temp-repo tests when `configs/paths.yaml` was absent.

### Assumptions made
- Sample-scale `workspace/final/*` artifacts remain traceability artifacts, not production proof.
- The canonical identity artifact remains read-only and anchors all compatibility behavior.
- Manual training/eval notebooks should create evidence trees only when the explicit execution gate is enabled.

### Decisions made
- Canonical identity resolution now prefers `sft_dataset.jsonl` / `preference_dataset.jsonl` everywhere and accepts old names only as aliases.
- Full-dataset manifest rendering always rebuilds validation from current inputs instead of trusting cached reports.
- Notebook 30 now uses shared selection logic and supports `ALLOW_SMALL_SAMPLE` without pretending to satisfy production token exactness.
- Notebooks 40/50/60 now write into `workspace/runs/<run_id>/...` evidence trees and align their default handoff paths through config.
- Deprecated script pipeline surfaces remain explicit notebook-routing shims with non-zero exit codes.

### Rationale
- The main failure mode in this repo was stale duplicated logic between docs, scripts, configs, and notebooks.
- Rebuilding validation from current inputs is safer than attempting partial cache invalidation for proof-bearing manifests.
- Evidence directories need to be config-driven and non-empty before any stage can claim completion.

### Risks / uncertainties introduced
- Notebook training cells still depend on heavyweight local runtime prerequisites (`unsloth`, TRL, GPU availability) that were not executed in this pass.
- `workspace/runs/` remains empty, so the new evidence contract is implemented but not yet proven by a real SFT/DPO/eval/export run.
- Existing sample `workspace/final/*` outputs still reflect legacy sample composition and intentionally fail exact identity token-share checks outside sample mode.

### Rollback / recovery notes
- If notebook evidence behavior causes operator friction, revert notebook 40/50/60 to non-executing descriptive state rather than reintroducing stale direct-path defaults.
- If manifest consumers break on the current schema, keep the new manifest as canonical and demote legacy readers instead of restoring the stale shape.

### Next recommended step
- Execute a real notebook 40 SFT run into `workspace/runs/<run_id>/`, then a notebook 50 DPO run and notebook 60 eval/export pass so the repo gains first-class proof-bearing training evidence instead of only readiness scaffolding.

## Entry 2026-03-08 09:15:21 +02:00 — Session rehab-20260308-02

### Objective
- Add a single Colab-first main notebook that runs the active Lumis-1 path sequentially from identity input through dataset build, SFT, DPO, GGUF export, and downloadable artifacts.

### Repository areas inspected
- `notebooks/20_build_open_dataset_mix.ipynb`
- `notebooks/30_merge_and_validate_full_dataset.ipynb`
- `notebooks/40_train_sft_unsloth_qwen35_4b.ipynb`
- `notebooks/50_train_dpo_unsloth_qwen35_4b.ipynb`
- `notebooks/60_eval_export_smoke.ipynb`
- `configs/train_sft.yaml`
- `configs/train_dpo.yaml`
- `requirements.txt`
- `constraints.txt`
- `lumis1/export_smoke.py`
- historical export metadata under `archive/legacy_generated/...`

### Files modified
- Pending implementation.

### Commands executed
```bash
# Context7 queries for Unsloth install/export and TRL DPOTrainer setup
# notebook cell extraction for notebooks 20/30/40/50/60
# rg search for GGUF/export implementation
# inspection of archive export metadata
```

### Outputs / reports produced
- Colab-main design constraints and dependency findings gathered.

### Bugs / errors observed
- Active path still lacks a real GGUF export implementation; notebook 60 only smoke-checks existing GGUF artifacts.
- Current training notebooks still rely on config-driven output directories, so a single Colab notebook needs runtime overrides to avoid manual config editing per run.

### Assumptions made
- Colab execution must be strictly sequential and cannot rely on multiple notebooks being open or run in parallel.
- The operator will provide one canonical identity dataset folder and expects the notebook to derive the repo-local path layout from it.

### Decisions made
- Use repo-pinned dependencies by default for Colab and treat Unsloth auto-install as a fallback only if notebook 00 environment checks fail.
- Implement a small run-plan/runtime override helper with tests before creating the orchestration notebook.
- Use Unsloth's supported GGUF save path for export instead of inventing a separate llama.cpp-only pipeline.

### Rationale
- A single notebook should reuse the active path semantics, not create a second incompatible training/export path.
- The export requirement is user-critical and needs an active implementation, not just smoke-check reporting.

### Risks / uncertainties introduced
- Colab package images can drift relative to repo constraints and may still require fallback install handling.
- GGUF export from the post-DPO artifact depends on Unsloth correctly loading the saved model directory in Colab.

### Rollback / recovery notes
- If the all-in-one notebook becomes too brittle, keep the new helper module and demote the notebook to an orchestrated tutorial surface rather than deleting the safer runtime additions.

### Next recommended step
- Add failing tests for the Colab run-plan/runtime-override helper and then implement the helper plus the single orchestration notebook.

## Entry 2026-03-08 09:36:51 +02:00 — Session rehab-20260308-03

### Objective
- Add a single sequential Colab notebook for the active Lumis-1 path, with user-supplied identity folder input, repo-pinned dependency defaults, GGUF-first export, and end-of-run artifact copy/download support.

### Repository areas inspected
- `requirements.txt`
- `constraints.txt`
- `PROJECT_BRIEF.md`
- `STATE.yaml`
- `LOG.md`
- `OPERATOR_RUN_ORDER.md`
- `notebooks/20_build_open_dataset_mix.ipynb`
- `notebooks/30_merge_and_validate_full_dataset.ipynb`
- `notebooks/40_train_sft_unsloth_qwen35_4b.ipynb`
- `notebooks/50_train_dpo_unsloth_qwen35_4b.ipynb`
- `notebooks/60_eval_export_smoke.ipynb`
- `lumis1/full_dataset.py`
- `lumis1/identity_pack.py`
- `lumis1/export_smoke.py`
- `lumis1/run_evidence.py`
- `tests/test_colab_main_notebook.py`

### Files modified
- `scripts/build_colab_main_notebook.py`
- `notebooks/90_colab_main_pipeline.ipynb`
- `tests/test_colab_main_notebook.py`
- `PROJECT_BRIEF.md`
- `STATE.yaml`
- `OPERATOR_RUN_ORDER.md`
- `LOG.md`
- `PROJECT_CHANGELOG_DETAILED.md`
- `PROJECT_TIME_CAPSULE.md`

### Commands executed
```bash
python scripts/build_colab_main_notebook.py
python -m py_compile scripts/build_colab_main_notebook.py
python -m pytest tests/test_colab_main_notebook.py -q
python -m pytest -q
python - <<'PY'
import json
from pathlib import Path
for path in sorted(Path("notebooks").glob("*.ipynb")):
    nb = json.loads(path.read_text(encoding="utf-8"))
    for idx, cell in enumerate(nb.get("cells", [])):
        if cell.get("cell_type") == "code":
            compile("".join(cell.get("source", [])), f"{path}#cell{idx}", "exec")
print("compiled notebooks")
PY
```

### Outputs / reports produced
- `notebooks/90_colab_main_pipeline.ipynb`
- `scripts/build_colab_main_notebook.py`
- updated Colab notebook regression test coverage

### Bugs / errors observed
- A full one-shot patch for the notebook generator exceeded Windows command-length limits with `Io(Os { code: 206, kind: InvalidFilename, message: "The filename or extension is too long." })`.

### Assumptions made
- The operator wants one sequential Colab surface, not another script-only execution path.
- The canonical identity dataset will be mounted or copied into a Drive-backed folder and should remain read-only.
- GGUF export must be treated as primary; merged 16-bit output is only a fallback artifact for recovery when direct GGUF export fails.

### Decisions made
- Generated the new notebook from `scripts/build_colab_main_notebook.py` instead of hand-editing notebook JSON.
- Kept the modular notebook chain as the underlying canonical logic and documented notebook 90 as a convenience wrapper.
- Defaulted the Colab surface to the repo-pinned dependency baseline and documented Unsloth auto-install as fallback only.
- Used runtime-derived run ids and output directories inside notebook 90 so Colab operators do not have to edit `train_sft.yaml` and `train_dpo.yaml` for each run.
- Made direct `save_pretrained_gguf` the first export path and required q8_0 plus q4 output variants before export can claim completion.

### Rationale
- A generated notebook is easier to review, regenerate, and keep aligned with the active runtime than hand-maintained JSON.
- The user explicitly cannot run multiple notebooks simultaneously, so a sequential orchestration surface is justified.
- Repo-pinned dependencies are more trustworthy than blind latest-package installs in ephemeral Colab environments.

### Risks / uncertainties introduced
- Notebook 90 is statically verified but still unproven by a real Colab execution on the requested GA6 runtime.
- Direct GGUF export success still depends on Unsloth runtime compatibility with the saved SFT/DPO artifact on Colab.
- Export smoke remains partial unless the operator also supplies `workspace/reports/template_parity_pairs.json` or another GGUF inference surface.

### Rollback / recovery notes
- Regenerate notebook 90 by rerunning `python scripts/build_colab_main_notebook.py` after any future notebook-generator edits.
- If the Colab orchestration surface drifts, demote it before changing the modular canonical notebooks.

### Next recommended step
- Run `notebooks/90_colab_main_pipeline.ipynb` on Colab with a real identity folder, confirm `workspace/runs/<run_id>/artifacts/gguf/` contains both q8_0 and q4 variants, and only then treat the new single-notebook path as operationally proven.

## Entry 2026-03-08 09:52:06 +02:00 — Session rehab-20260308-04

### Objective
- Re-audit the single Colab notebook against current official Unsloth and TRL guidance for Qwen3.5 non-thinking behavior, package installation drift, and GGUF export handling, then harden the notebook to fail fast instead of failing late.

### Repository areas inspected
- `notebooks/90_colab_main_pipeline.ipynb`
- `scripts/build_colab_main_notebook.py`
- `tests/test_colab_main_notebook.py`
- `lumis1/main_pipeline.py`
- `workspace/reports/identity_validation.json`
- `workspace/reports/full_dataset_validation.json`
- official Unsloth docs / README / wiki
- official Qwen3.5 Hugging Face model card signals for `enable_thinking=False`
- official TRL docs for `SFTTrainer` and `DPOTrainer`

### Files modified
- `notebooks/90_colab_main_pipeline.ipynb`
- `scripts/build_colab_main_notebook.py`
- `tests/test_colab_main_notebook.py`
- `PROJECT_BRIEF.md`
- `STATE.yaml`
- `LOG.md`
- `PROJECT_CHANGELOG_DETAILED.md`
- `PROJECT_TIME_CAPSULE.md`

### Commands executed
```bash
python -m pytest tests/test_colab_main_notebook.py -q
python -m pytest -q
python -m py_compile scripts/build_colab_main_notebook.py
python scripts/build_colab_main_notebook.py
python - <<'PY'
import json
from pathlib import Path
for path in sorted(Path("notebooks").glob("*.ipynb")):
    nb = json.loads(path.read_text(encoding="utf-8"))
    for idx, cell in enumerate(nb.get("cells", [])):
        if cell.get("cell_type") == "code":
            compile("".join(cell.get("source", [])), f"{path}#cell{idx}", "exec")
print("compiled notebooks")
PY
```

### Outputs / reports produced
- hardened `notebooks/90_colab_main_pipeline.ipynb`
- updated Colab notebook compile/test evidence

### Bugs / errors observed
- notebook 90 initially failed compile checks due broken newline escaping in string literals introduced during hardening edits
- `scripts/build_colab_main_notebook.py` was in a stale state that could have rewritten notebook 90 to an empty placeholder if run blindly
- repository evidence confirms the merged dataset contains multimodal rows (`image_text_rows > 0`), while the current Colab SFT path is still only trustworthy as a language-path implementation

### Assumptions made
- Official Qwen3.5 non-thinking behavior should be enforced through tokenizer chat-template rendering with `enable_thinking=False`, not by relying on informal prompt hacks
- Failing early on an unverified multimodal training path is safer than letting Colab fail hours later

### Decisions made
- Added strict repo-pinned environment synchronization checks for Colab installs
- Added tokenizer-level non-thinking probes before SFT, DPO, and eval generation surfaces
- Switched eval prompt construction to chat-template rendering instead of raw prompt strings
- Added a default multimodal SFT refusal when image-text rows are present and the operator has not explicitly allowed the unverified path
- Changed the notebook helper script so it preserves and normalizes the canonical notebook instead of creating an empty shell

### Rationale
- The highest-probability late failures on Colab were environment drift and Qwen3.5 chat-template misuse
- The most serious hidden correctness issue was that the merged dataset is multimodal while the currently proven training code path is not yet evidence-backed as an explicit FastVisionModel implementation

### Risks / uncertainties introduced
- The notebook is now safer but more conservative; by default it will stop before multimodal SFT rather than pretending that path is proven
- An end-to-end multimodal Qwen3.5 Colab path still needs a separate FastVisionModel implementation and proof run

### Rollback / recovery notes
- If the new guard is too strict for exploratory work, operators can toggle `ALLOW_UNVERIFIED_MULTIMODAL_SFT = True`, but that must not be treated as proof-bearing execution
- If notebook 90 is ever corrupted, rerun `python scripts/build_colab_main_notebook.py` only after verifying the canonical notebook file already exists

### Next recommended step
- Either implement the explicit FastVisionModel multimodal SFT path for Qwen3.5 and verify it on Colab, or intentionally constrain the all-in-one notebook to a text-only verified training path before claiming it is foolproof.

## Entry 2026-03-08 10:15:01 +02:00 — Session rehab-20260308-05

### Objective
- Review the high-severity findings on the single Colab pipeline, repair the concrete contract mismatches, and re-verify the notebook/runtime/test surface before any push.

### Repository areas inspected
- `notebooks/90_colab_main_pipeline.ipynb`
- `notebooks/30_merge_and_validate_full_dataset.ipynb`
- `notebooks/50_train_dpo_unsloth_qwen35_4b.ipynb`
- `lumis1/main_pipeline.py`
- `lumis1/schema.py`
- `lumis1/identity_pack.py`
- `scripts/build_colab_main_notebook.py`
- `tests/test_schema.py`
- `tests/test_main_pipeline.py`
- `tests/test_colab_main_notebook.py`
- `workspace/reports/full_dataset_validation.json`
- official Unsloth, TRL, Transformers, and Qwen sources

### Files modified
- `lumis1/schema.py`
- `lumis1/main_pipeline.py`
- `notebooks/30_merge_and_validate_full_dataset.ipynb`
- `notebooks/50_train_dpo_unsloth_qwen35_4b.ipynb`
- `notebooks/90_colab_main_pipeline.ipynb`
- `scripts/build_colab_main_notebook.py`
- `tests/test_schema.py`
- `tests/test_main_pipeline.py`
- `tests/test_colab_main_notebook.py`
- `PROJECT_BRIEF.md`
- `STATE.yaml`
- `LOG.md`
- `PROJECT_CHANGELOG_DETAILED.md`
- `PROJECT_TIME_CAPSULE.md`

### Commands executed
```bash
python -m pytest tests/test_schema.py tests/test_main_pipeline.py tests/test_colab_main_notebook.py -q
python -m pytest -q
python -m py_compile scripts/build_colab_main_notebook.py
python scripts/build_colab_main_notebook.py
python - <<'PY'
import json
from pathlib import Path
for path in sorted(Path("notebooks").glob("*.ipynb")):
    nb = json.loads(path.read_text(encoding="utf-8"))
    for idx, cell in enumerate(nb.get("cells", [])):
        if cell.get("cell_type") == "code":
            compile("".join(cell.get("source", [])), f"{path}#cell{idx}", "exec")
print("compiled 8 notebooks")
PY
git status --short
```

### Outputs / reports produced
- updated `notebooks/90_colab_main_pipeline.ipynb`
- updated `workspace/reports/train_dpo_config_resolved.json` expectations via notebook/runtime parity
- refreshed notebook compile evidence

### Bugs / errors observed
- notebook 90 and notebook 50 briefly failed compile checks because multi-line string literals were written with broken newline escaping during a first edit pass
- the current merged preference dataset shape uses `prompt_messages`, while notebook 50 and notebook 90 DPO cells assumed a `prompt` string
- notebook 90 bootstrap previously hardcoded `codex/truth-parity-rehab`, rejected documented identity-file aliases, and disagreed with `lumis1.main_pipeline` on the GGUF export run location

### Assumptions made
- The stable default branch for Colab bootstrap should be `main`, with environment override support for other branches.
- The multimodal SFT gap is still real and should remain an explicit stop condition instead of being papered over.
- Normalizing identity preference rows during merge is safer than teaching every downstream consumer to accept raw legacy identity preference shapes.

### Decisions made
- Extended `validate_preference_row` to accept `prompt_messages` and return a normalized `prompt`.
- Rewrote notebook 30 and notebook 90 merge steps so identity preference rows are normalized before `full_preferences.jsonl` is emitted.
- Repaired notebook 50 and notebook 90 DPO paths so they normalize prompts from either `prompt` or `prompt_messages`.
- Moved the authoritative GGUF export contract in `lumis1.main_pipeline` to the dedicated `*-export` run.
- Replaced the hardcoded feature-branch bootstrap in notebook 90 and the helper script with env-selectable branch/repo inputs, defaulting to `main`.
- Made notebook 90 bootstrap accept both canonical identity filenames and documented aliases.

### Rationale
- The DPO prompt-shape mismatch was a direct runtime bug against the repo’s own merged sample outputs.
- The branch/bootstrap/export-layout mismatches would have caused silent drift or false-negative artifact discovery in the main Colab path.
- These fixes improve internal coherence without pretending the unverified multimodal SFT path is solved.

### Risks / uncertainties
- The single Colab notebook is still not a proof-bearing multimodal Qwen3.5 trainer; it remains a guarded surface until a real FastVisionModel path is implemented and executed.
- Defaulting the bootstrap branch to `main` assumes the pushed repo will carry the repaired notebook there.

### Rollback / recovery notes
- If the branch-default change is inconvenient for staging, set `LUMIS1_REPO_BRANCH` in Colab instead of re-hardcoding a feature branch.
- If the DPO prompt normalization causes unexpected trainer behavior, the canonical merged preferences can be inspected in `workspace/final/full_preferences.jsonl` before training.

### Next recommended step
- Implement and verify the explicit FastVisionModel multimodal SFT path, or formally narrow notebook 90 to a text-only training scope before presenting it as end-to-end runnable on the repo’s current multimodal dataset.

## 2026-03-08T10:32:00+02:00 | session: notebook-path-correction

### Intent / objective
- Correct operator-facing confusion after an uncommitted detour created the wrong instruction document and left a stale remote branch alive.

### Repository areas inspected
- `notebooks/`
- `LOG.md`
- `PROJECT_CHANGELOG_DETAILED.md`
- `PROJECT_TIME_CAPSULE.md`
- git branch state

### Files modified
- `LOG.md`
- `NOTEBOOK_OPERATOR_INSTRUCTIONS.md`
- `PROJECT_CHANGELOG_DETAILED.md`
- `PROJECT_TIME_CAPSULE.md`

### Files removed
- `REPO_RELINK_AND_PUSH_MAIN_INSTRUCTIONS.md`

### Commands executed
```bash
git status --short
git branch -a
git log --oneline --decorate -n 5
git diff -- LOG.md
git show HEAD:notebooks/90_colab_main_pipeline.ipynb
```

### Outputs / reports produced
- `NOTEBOOK_OPERATOR_INSTRUCTIONS.md`

### Bugs / errors observed
- The unified notebook itself was present on `main`, but a later uncommitted instruction-doc edit path created avoidable confusion.
- `origin/codex/truth-parity-rehab` remained after `main` had already absorbed the rehab work.

### Assumptions made
- The user wanted a notebook-focused operator instruction document, not a repo-relink procedure.

### Decisions made
- Removed the mistaken relink instruction document before it could be committed.
- Added a notebook-focused instruction document that points directly to notebook 90 and clarifies proven vs unproven state.

### Rationale for decisions
- The current confusion was about notebook discoverability and execution surface, not git relinking.

### Risks or uncertainties
- The operator documentation is now clearer, but notebook 90 still remains operationally limited by the unproven multimodal SFT path.

### Rollback / recovery notes
- If a repo-relink procedure is needed later, recreate it in a separate historical/admin document instead of mixing it with notebook operator guidance.

### Next recommended step
- Delete the stale remote rehab branch so only `main` remains on the remote, then commit and push the notebook-instruction correction.

## 2026-03-08T10:37:00+02:00 | session: notebook-wording-fix

### Intent / objective
- Remove the last contradictory wording inside notebook 90 after `main` became the default branch.

### Repository areas inspected
- `notebooks/90_colab_main_pipeline.ipynb`
- `NOTEBOOK_OPERATOR_INSTRUCTIONS.md`

### Files modified
- `notebooks/90_colab_main_pipeline.ipynb`
- `NOTEBOOK_OPERATOR_INSTRUCTIONS.md`
- `PROJECT_CHANGELOG_DETAILED.md`
- `PROJECT_TIME_CAPSULE.md`

### Commands executed
```bash
git show HEAD:notebooks/90_colab_main_pipeline.ipynb
```

### Bugs / errors observed
- The notebook markdown still said it bootstrapped the rehab branch even though the implementation now defaults to `main`.

### Decisions made
- Updated the notebook wording to match the current bootstrap behavior.
- Added the absolute notebook path to the operator instruction document for direct discoverability.

### Rationale for decisions
- The contradiction made a valid notebook look untrustworthy and directly contributed to operator confusion.

### Risks or uncertainties
- This fixes discoverability and wording only; it does not change the unresolved multimodal SFT limitation.

### Next recommended step
- Push the notebook wording fix to `main`.

## 2026-03-08T10:54:56+02:00 | session: colab-single-pass-hardening

### Intent / objective
- Harden the unified Colab notebook against the concrete failure modes found in a hostile audit, with emphasis on one-pass execution and reduced operator intervention.

### Repository areas inspected
- `notebooks/90_colab_main_pipeline.ipynb`
- `lumis1/main_pipeline.py`
- `lumis1/run_evidence.py`
- `scripts/build_colab_main_notebook.py`
- `tests/test_colab_main_notebook.py`
- `tests/test_main_pipeline.py`
- `tests/test_run_evidence.py`
- official Unsloth, TRL, and Qwen sources

### Files modified
- `notebooks/90_colab_main_pipeline.ipynb`
- `lumis1/main_pipeline.py`
- `lumis1/run_evidence.py`
- `scripts/build_colab_main_notebook.py`
- `tests/test_colab_main_notebook.py`
- `tests/test_main_pipeline.py`
- `tests/test_run_evidence.py`
- `PROJECT_BRIEF.md`
- `STATE.yaml`
- `LOG.md`
- `NOTEBOOK_OPERATOR_INSTRUCTIONS.md`
- `PROJECT_CHANGELOG_DETAILED.md`
- `PROJECT_TIME_CAPSULE.md`

### Commands executed
```bash
python scripts/build_colab_main_notebook.py
python -m pytest tests/test_main_pipeline.py tests/test_colab_main_notebook.py -q
python -m pytest -q
python - <<'PY'
import json
from pathlib import Path
p = Path("notebooks/90_colab_main_pipeline.ipynb")
nb = json.loads(p.read_text(encoding="utf-8"))
for idx, cell in enumerate(nb["cells"]):
    if cell.get("cell_type") == "code":
        compile("".join(cell.get("source", [])), f"{p}#cell{idx}", "exec")
print("compiled notebook 90")
PY
```

### Outputs / reports produced
- hardened `notebooks/90_colab_main_pipeline.ipynb`
- updated notebook operator guidance
- updated regression tests for the single-pass Colab path

### Bugs / errors observed
- notebook 90 previously hard-killed the Colab runtime during dependency installation and required a manual rerun
- notebook 90 defaulted to a 96 GB profile with no auto-downgrade for smaller GPUs
- notebook 90 blocked on placeholder-only image rows even though the runtime already had a text-only fallback helper
- notebook 90 assumed merged/full-model checkpoints for DPO and eval even when upstream stages saved PEFT adapters
- GGUF export fallback previously stopped after producing a merged directory and never retried GGUF conversion from that merged model
- notebook builder failed on notebook BOM decoding and had drifted away from the actual notebook contract

### Assumptions made
- A single-pass Colab run should prefer a safer automatic profile on smaller GPUs rather than assuming a 96 GB device class.
- Placeholder-only image rows may be collapsed to a text-only training surface without claiming proof-bearing multimodal training.
- `structural_only` export completion is acceptable for unattended runs when required GGUF variants exist but parity-pair inputs are absent, as long as this weaker status is labeled explicitly.

### Decisions made
- Added `resolve_profile_name`, `detect_model_artifact_layout`, and message normalization helpers to the shared runtime.
- Removed the forced install-time kernel kill from notebook 90 and replaced it with in-place dependency convergence checks.
- Auto-collapsed placeholder-only image rows into a text-only SFT fallback in notebook 90.
- Made DPO, eval, and export adapter-aware by detecting PEFT artifact layouts explicitly.
- Allowed `multimodal_correctness = not_applicable` and `export_smoke = structural_only` as unattended completion states in run-status assessment.
- Fixed the notebook builder to read notebook 90 with BOM-tolerant decoding.

### Rationale for decisions
- These changes remove operator-intervention traps without pretending the unresolved concrete multimodal training gap is solved.
- The explicit weaker statuses preserve honesty while making the unified notebook usable for the currently automatable path.

### Risks or uncertainties
- Concrete multimodal SFT remains unverified and still cannot be called proof-bearing.
- `structural_only` export completion is weaker than parity-verified GGUF smoke and may not be sufficient for final release criteria.
- Open-corpus assembly still has order-sensitive exact-token-budget constraints that can fail on upstream dataset drift.

### Rollback / recovery notes
- If unattended completion proves too permissive, tighten `assess_eval_export_status` again by removing `not_applicable` or `structural_only` from the accepted status set.
- If Colab import behavior regresses after in-place installs, reintroduce a restart only as a guarded fallback for already-imported runtime packages.

### Next recommended step
- Run notebook 90 on a real Colab G4 session and record whether the one-pass path reaches SFT, DPO, GGUF export, and eval without manual resets.

## Entry 2026-03-08 11:31:36 +02:00 — Session rehab-20260308-06

### Objective
- Re-implement notebook 90 as a standalone Colab notebook with embedded configs/runtime, real multimodal materialization steps, and a full single-pass SFT -> DPO -> GGUF -> eval flow.

### Repository areas inspected
- `notebooks/90_colab_main_pipeline.ipynb`
- `scripts/build_colab_main_notebook.py`
- `lumis1/colab_standalone.py`
- `lumis1/main_pipeline.py`
- `lumis1/vision_schema.py`
- `lumis1/schema.py`
- `notebooks/20_build_open_dataset_mix.ipynb`
- `notebooks/30_merge_and_validate_full_dataset.ipynb`
- `configs/dataset_mixture.yaml`
- `configs/dataset_sources_allowlist.yaml`
- `configs/train_sft.yaml`
- `configs/train_dpo.yaml`
- `workspace/reports/identity_validation.json`
- `workspace/reports/full_dataset_validation.json`
- `workspace/reports/open_corpus_build_report.json`
- canonical identity artifact under `Dataset/identity_dataset/output/full_run_codex_spark_xhigh/`

### Files modified
- `lumis1/colab_standalone.py`
- `tests/test_colab_standalone.py`
- `tests/test_colab_main_notebook.py`
- `scripts/build_colab_main_notebook.py`
- `notebooks/90_colab_main_pipeline.ipynb`
- `PROJECT_BRIEF.md`
- `STATE.yaml`
- `LOG.md`
- `NOTEBOOK_OPERATOR_INSTRUCTIONS.md`
- `PROJECT_CHANGELOG_DETAILED.md`
- `PROJECT_TIME_CAPSULE.md`

### Commands executed
```bash
# Context7 query for Transformers multimodal chat templating
# Context7 query for Unsloth FastVisionModel examples
# Get-Content / rg over notebook 90, notebook 20, notebook 30, lumis1/*.py, reports, identity artifact
# Get-Content workspace/final/full_sft.jsonl -TotalCount 5
# Get-Content workspace/interim/open_sft.jsonl -TotalCount 5
# Get-ChildItem / rg over Dataset/identity_dataset/output/full_run_codex_spark_xhigh
# python -m pytest tests/test_colab_standalone.py tests/test_colab_main_notebook.py -q
# python scripts/build_colab_main_notebook.py
# python -m pytest -q
# notebook JSON/code-cell compile sweep across all notebooks
# python -m py_compile scripts/build_colab_main_notebook.py lumis1/colab_standalone.py
```

### Outputs / reports produced
- Rebuilt `notebooks/90_colab_main_pipeline.ipynb` as a standalone notebook.
- Added the embedded-runtime helper module `lumis1/colab_standalone.py`.
- Added regression coverage in `tests/test_colab_standalone.py`.
- Updated operator/state/docs to describe the standalone notebook truthfully.

### Bugs / errors observed
- The previous notebook 90 was not standalone and still imported repo-side modules/config files.
- The previous notebook 90 collapsed placeholder image rows to text-only instead of providing a real multimodal path.
- The current merged sample artifacts still use placeholder URIs (`image://...`, `synthetic://...`) rather than concrete image payloads.
- The canonical identity artifact itself only stores placeholder multimodal references, so a true multimodal run needs asset materialization before SFT.
- The first generator rewrite produced an `IndentationError` because pretty-printed embedded JSON broke notebook cell dedenting; fixed by switching to single-line embedded JSON literals.

### Assumptions made
- Placeholder identity image references can be bridged operationally with deterministic surrogate screenshot/document images for notebook-run training.
- Supported HF multimodal sources will expose image payloads consumable by `datasets` at Colab runtime.
- Text-preference DPO remains acceptable on top of the multimodal base model path.

### Decisions made
- Rebuild notebook 90 as a self-contained runtime surface instead of patching the old repo-dependent cells again.
- Embed config YAML text and a tested runtime helper module directly into notebook 90.
- Materialize placeholder identity images into concrete local `image_path` files instead of silently dropping multimodal rows.
- Use `FastVisionModel` + `UnslothVisionDataCollator` for SFT whenever concrete multimodal rows exist.
- Keep DPO text-preference oriented but make the handoff and evidence contract consistent inside the same notebook.
- Treat the notebook as operationally stronger but still unproven until a real Colab G4 run succeeds.

### Rationale
- The user explicitly required a notebook that can run without attaching repo-side YAML files.
- The biggest correctness gap was not UI convenience but the absence of a real multimodal dataset-to-trainer path.
- The identity artifact is still the strongest completed dataset artifact, so the notebook has to adapt around it rather than rewriting it.

### Risks / uncertainties
- Identity multimodal rows are still trained against surrogate images, not curated original screenshots/documents.
- HF multimodal source schemas may drift at runtime; the embedded mapping is heuristic and statically tested only.
- GGUF export remains structurally verified by the code path, not proven on a real Colab run in this repo.
- The DPO stage still optimizes text preferences, not multimodal preference data.

### Rollback / recovery notes
- If notebook 90 proves less reliable than the modular path on Colab, revert to the canonical `00 -> 10 -> 20 -> 30 -> 40 -> 50 -> 60` sequence and keep notebook 90 labeled convenience-only.
- If surrogate identity images are judged unacceptable, disable multimodal identity SFT until curated real identity images exist.

### Next recommended step
- Run `notebooks/90_colab_main_pipeline.ipynb` on a real Colab G4 runtime with the canonical identity folder under Drive, then inspect `workspace/runs/<run_id>/`, `workspace/reports/open_corpus_build_report.json`, `workspace/reports/full_dataset_validation.json`, and the GGUF export directory before making any claim that the notebook is proof-bearing.

## Entry 2026-03-08 11:42:49 +02:00 — Session rehab-20260308-07

### Objective
- Critique the rebuilt standalone notebook like a hostile reviewer, then fix any remaining concrete Colab G4 runtime hazards before closing.

### Repository areas inspected
- `scripts/build_colab_main_notebook.py`
- `notebooks/90_colab_main_pipeline.ipynb`
- `lumis1/colab_standalone.py`
- `requirements.txt`
- `constraints.txt`
- `tests/test_colab_main_notebook.py`
- `tests/test_colab_standalone.py`
- `PROJECT_BRIEF.md`
- `STATE.yaml`
- `LOG.md`

### Files modified
- `requirements.txt`
- `constraints.txt`
- `scripts/build_colab_main_notebook.py`
- `notebooks/90_colab_main_pipeline.ipynb`
- `tests/test_colab_main_notebook.py`
- `PROJECT_BRIEF.md`
- `STATE.yaml`
- `LOG.md`
- `PROJECT_CHANGELOG_DETAILED.md`
- `PROJECT_TIME_CAPSULE.md`

### Commands executed
```bash
# python -m pytest -q
# python -m pytest tests/test_colab_main_notebook.py tests/test_colab_standalone.py -q
# python scripts/build_colab_main_notebook.py
# notebook JSON/code-cell compile sweep for notebooks/*.ipynb
# rg / Get-Content over scripts/build_colab_main_notebook.py, requirements.txt, constraints.txt, notebook 90
# Get-Date -Format o
```

### Outputs / reports produced
- Rebuilt `notebooks/90_colab_main_pipeline.ipynb` with embedded requirements-plus-constraints install content.
- Refreshed notebook/operator state in `PROJECT_BRIEF.md`, `STATE.yaml`, and `LOG.md`.

### Bugs / errors observed
- Notebook 90 was still embedding only `constraints.txt`, not the actual requirement surface, so a fresh Colab could miss packages like `huggingface-hub`, `sentencepiece`, or `safetensors`.
- The multimodal SFT/export/eval path still treated the returned preprocessing object too much like a plain tokenizer and did not persist processor assets explicitly.
- The export path still preferred generic PEFT merge first even for multimodal adapters, which was a weaker fit for the current Unsloth vision save/load surface.

### Assumptions made
- Explicitly embedding `requirements.txt` plus `constraints.txt` is a more faithful standalone install contract than embedding only constraint pins.
- Persisting processor assets alongside adapters and merged artifacts reduces the odds of silent multimodal reload/export failure on Colab.

### Decisions made
- Add `huggingface-hub` to the explicit dependency surface and pin it in `constraints.txt`.
- Keep `safetensors` explicitly pinned in `constraints.txt` because notebook 90 now installs from requirements plus constraints.
- Change notebook 90 to embed both requirement and constraint text and install via `pip install -r ... -c ...`.
- Add helper functions for tokenizer/processor loading and processing-asset persistence in the embedded notebook runtime.
- Prefer `FastVisionModel.save_pretrained_merged` / `FastLanguageModel.save_pretrained_merged` before falling back to generic `AutoPeftModelForCausalLM.merge_and_unload`.

### Rationale
- A self-contained notebook cannot truthfully depend on packages being present only because Colab happened to preinstall them.
- Multimodal save/load/export failures usually show up late and expensively; persisting processor assets and preferring Unsloth-native merge reduces that class of breakage before the first real run.

### Risks / uncertainties
- The HF multimodal source mapping is still heuristic and still unproven on a real Colab G4 run.
- The merged multimodal export path is statically hardened, not proof-bearing yet.
- Surrogate identity images remain an operational bridge, not equivalent to curated real images.

### Rollback / recovery notes
- If the embedded requirements-plus-constraints install proves too strict for Colab, narrow the pinned surface only after capturing the exact package conflict in `workspace/runs/<run_id>/environment/`.
- If Unsloth-native merged export fails on a real run, keep the current generic PEFT fallback and record the exact failure string before changing the precedence order again.

### Next recommended step
- Run notebook 90 on a real Colab G4 session and verify that the embedded install completes, multimodal SFT saves processor assets, and GGUF export can reload the merged artifact without manual intervention.

## Entry 2026-03-08 11:44:12 +02:00 — Session rehab-20260308-08

### Objective
- Critique the standalone notebook again after the rebuild and remove remaining multimodal handoff bugs in DPO, export, and eval.

### Repository areas inspected
- `scripts/build_colab_main_notebook.py`
- `notebooks/90_colab_main_pipeline.ipynb`
- `tests/test_colab_main_notebook.py`
- `PROJECT_BRIEF.md`
- `STATE.yaml`
- `LOG.md`

### Files modified
- `scripts/build_colab_main_notebook.py`
- `notebooks/90_colab_main_pipeline.ipynb`
- `tests/test_colab_main_notebook.py`
- `STATE.yaml`
- `LOG.md`
- `PROJECT_CHANGELOG_DETAILED.md`
- `PROJECT_TIME_CAPSULE.md`

### Commands executed
```bash
# python scripts/build_colab_main_notebook.py
# python -m py_compile scripts/build_colab_main_notebook.py lumis1/colab_standalone.py
# python -m pytest tests/test_colab_main_notebook.py tests/test_colab_standalone.py -q
# python -m pytest -q
# notebook JSON/code-cell compile sweep for notebooks/*.ipynb
# rg / Get-Content over scripts/build_colab_main_notebook.py and generated notebook 90
```

### Outputs / reports produced
- Regenerated `notebooks/90_colab_main_pipeline.ipynb` from the patched generator.
- Refreshed notebook contract verification with `47 passed` overall and `5 passed` for the notebook-specific subset.

### Bugs / errors observed
- Notebook 90 still assumed a successful DPO handoff when picking the final model for export/eval.
- The GGUF export cell skipped direct Unsloth export attempts whenever the generic PEFT merge step failed, even though the adapter directory could still be a valid direct export input.
- The eval cell still assumed the causal-loader path would always work for the effective final model.

### Assumptions made
- Export/eval should continue from the best available artifact even if DPO fails, as long as the failure is recorded in run evidence.
- A direct Unsloth loader retry from adapter directories is a safer fallback than aborting export immediately after a failed generic merge.

### Decisions made
- Make DPO fail closed: record failure in run evidence, keep the notebook running, and fall back to the SFT artifact for downstream stages.
- Change export to retry direct Unsloth loads from both the merged directory and the original final-model directory.
- Change eval to follow the effective final model and fall back to a `FastVisionModel` loader when the causal-loader path fails.
- Extend notebook contract tests so the generated notebook must contain the new fallback surfaces.

### Rationale
- The previous behavior turned recoverable multimodal handoff failures into full-run aborts.
- A one-notebook unattended Colab surface has to degrade explicitly and traceably rather than silently assuming every intermediate stage succeeded.

### Risks / uncertainties
- The new DPO/export/eval fallbacks are still statically verified only; no real Colab G4 evidence exists yet.
- Multimodal DPO remains operationally tolerated, not evidence-backed.
- The fallback `FastVisionModel` eval path still depends on live processor/model compatibility at Colab runtime.

### Rollback / recovery notes
- If the DPO fail-closed behavior masks an issue you want to treat as fatal, restore the earlier hard-fail behavior only after capturing a real failing Colab run under `workspace/runs/<run_id>/`.
- If direct Unsloth export retries create ambiguous artifact states, inspect `workspace/runs/<run_id>/reports/gguf_export.json` before changing precedence again.

### Next recommended step
- Run notebook 90 on Colab G4 and inspect whether DPO completes, whether export uses a merged or adapter retry path, and whether eval uses the causal or `FastVisionModel` loader path in the generated run evidence.
