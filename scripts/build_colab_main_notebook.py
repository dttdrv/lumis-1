from __future__ import annotations

import json
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = REPO_ROOT / "notebooks" / "90_colab_main_pipeline.ipynb"
RUNTIME_PATH = REPO_ROOT / "lumis1" / "colab_standalone.py"
CONFIG_NAMES = [
    "dataset_mixture.yaml",
    "dataset_sources_allowlist.yaml",
    "train_sft.yaml",
    "train_dpo.yaml",
    "run_profiles.yaml",
    "chat_template_policy.yaml",
]


def _src(text: str) -> list[str]:
    text = textwrap.dedent(text).strip("\n") + "\n"
    return text.splitlines(keepends=True)


def _compile_notebook_code_cells(notebook: dict) -> None:
    for idx, cell in enumerate(notebook.get("cells", [])):
        if cell.get("cell_type") != "code":
            continue
        source = "".join(cell.get("source", []))
        compile(source, f"{OUTPUT_PATH}#cell{idx}", "exec")


def build_notebook() -> dict:
    runtime_source = RUNTIME_PATH.read_text(encoding="utf-8")
    embedded_configs = {
        name: (REPO_ROOT / "configs" / name).read_text(encoding="utf-8")
        for name in CONFIG_NAMES
    }
    requirements_text = (REPO_ROOT / "requirements.txt").read_text(encoding="utf-8")
    constraints_text = (REPO_ROOT / "constraints.txt").read_text(encoding="utf-8")

    cells: list[dict] = []
    cells.append(
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": _src(
                """
                # 90 Colab Main Pipeline

                Status: Canonical convenience surface | Draft

                This notebook is the single sequential Colab operator surface. It is designed to run on one runtime without depending on repo-side YAML files or Python modules being present outside the notebook itself.

                What it does:
                1. mounts Drive and sets one persistent working root
                2. installs the pinned environment in place
                3. materializes embedded configs and embedded runtime helpers from the notebook itself
                4. validates the identity dataset and rewrites placeholder identity image references into concrete local image paths
                5. streams the allowlisted open datasets, materializes real multimodal image rows where available, and writes one merged open corpus
                6. merges identity + open into one final dataset and writes proof-bearing reports
                7. runs multimodal SFT when concrete image paths exist
                8. runs text-preference DPO on the resulting model
                9. exports GGUF first
                10. runs text and multimodal eval plus export smoke
                11. copies the whole run evidence tree to Drive and can download one GGUF file to the browser

                Important truths:
                - the identity dataset still ships placeholder image references, so this notebook creates explicit surrogate document/screenshot assets for those rows before multimodal SFT
                - open multimodal rows are only trusted when they end up with concrete `image_path` values on disk
                - training, export, and eval are only proven when `workspace/runs/<run_id>/` is populated
                """
            ),
        }
    )
    cells.append(
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": _src(
                f"""
                from __future__ import annotations

                import json
                import os
                import shutil
                import subprocess
                import sys
                from pathlib import Path

                NOTEBOOK_SELF_CONTAINED = True
                WORK_ROOT = Path("/content/lumis1_main")
                DRIVE_ROOT = Path("/content/drive/MyDrive/lumis1_colab")
                IDENTITY_INPUT_DIR = DRIVE_ROOT / "identity_input"
                WORKSPACE_PERSIST_ROOT = DRIVE_ROOT / "workspace"
                EXPORT_PERSIST_ROOT = DRIVE_ROOT / "exports"
                IDENTITY_HF_REPO_ID = os.environ.get("LUMIS1_IDENTITY_HF_REPO", "STnoui/lumis1-identity")
                IDENTITY_AUTO_DOWNLOAD = True

                INSTALL_MODE = "repo_pinned"  # repo_pinned | unsloth_auto
                STRICT_REPO_PINNED_SYNC = True
                SOURCE_MODE = "hf"  # hf | local
                STREAMING = True
                DRY_RUN = False
                ALLOW_SMALL_SAMPLE = False

                PIPELINE_PREFIX = "colab-main-001"
                PROFILE = "auto"
                FIRST_50_STEPS_SANITY = False

                RUN_SFT = True
                RUN_DPO = True
                RUN_EXPORT = True
                RUN_EVAL = True

                GGUF_QUANTIZATION_METHODS = ["q4_k_m", "q8_0"]
                DOWNLOAD_GGUF_TO_BROWSER = False
                DOWNLOAD_GGUF_VARIANT_TOKEN = "q4_k_m"

                EVAL_DO_SAMPLE = True
                EVAL_TEMPERATURE = 0.7
                EVAL_TOP_P = 0.8
                EVAL_TOP_K = 20
                EVAL_SEED = 3407
                HF_TOKEN = os.environ.get("HF_TOKEN")

                EMBEDDED_REQUIREMENTS_TEXT = {json.dumps(requirements_text, ensure_ascii=False)}
                EMBEDDED_CONSTRAINTS_TEXT = {json.dumps(constraints_text, ensure_ascii=False)}
                EMBEDDED_CONFIG_TEXT = {json.dumps(embedded_configs, ensure_ascii=False)}
                EMBEDDED_RUNTIME_SOURCE = {json.dumps(runtime_source, ensure_ascii=False)}

                IN_COLAB = "google.colab" in sys.modules
                if IN_COLAB:
                    from google.colab import drive  # type: ignore

                    def mount_drive_safely(mountpoint: str = "/content/drive") -> None:
                        mount_path = Path(mountpoint)
                        if os.path.ismount(mountpoint):
                            return
                        if mount_path.exists():
                            if mount_path.is_symlink() or mount_path.is_file():
                                mount_path.unlink()
                            elif mount_path.is_dir() and any(mount_path.iterdir()):
                                shutil.rmtree(mount_path, ignore_errors=True)
                        try:
                            drive.mount(mountpoint, force_remount=False)
                        except ValueError as exc:
                            if "Mountpoint must not already contain files" not in str(exc):
                                raise
                            if mount_path.exists() and not os.path.ismount(mountpoint):
                                shutil.rmtree(mount_path, ignore_errors=True)
                            drive.mount(mountpoint, force_remount=True)

                    mount_drive_safely("/content/drive")
                    try:
                        from google.colab import userdata  # type: ignore
                        if HF_TOKEN is None:
                            HF_TOKEN = userdata.get("HF_TOKEN")
                    except Exception:
                        pass

                WORK_ROOT.mkdir(parents=True, exist_ok=True)
                WORKSPACE_PERSIST_ROOT.mkdir(parents=True, exist_ok=True)
                EXPORT_PERSIST_ROOT.mkdir(parents=True, exist_ok=True)
                os.chdir(WORK_ROOT)

                print(json.dumps({{
                    "work_root": str(WORK_ROOT),
                    "identity_input_dir": str(IDENTITY_INPUT_DIR),
                    "workspace_persist_root": str(WORKSPACE_PERSIST_ROOT),
                    "export_persist_root": str(EXPORT_PERSIST_ROOT),
                    "run_prefix": PIPELINE_PREFIX,
                    "profile": PROFILE,
                    "identity_hf_repo_id": IDENTITY_HF_REPO_ID,
                    "identity_auto_download": IDENTITY_AUTO_DOWNLOAD,
                    "run_sft": RUN_SFT,
                    "run_dpo": RUN_DPO,
                    "run_export": RUN_EXPORT,
                    "run_eval": RUN_EVAL,
                }}, indent=2))
                """
            ),
        }
    )
    cells.append(
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": _src(
                """
                from __future__ import annotations

                import importlib.metadata
                import subprocess
                import sys

                REQUIRED_MODULE_TO_PACKAGE = {
                    "yaml": "pyyaml",
                    "datasets": "datasets",
                    "transformers": "transformers",
                    "trl": "trl",
                    "accelerate": "accelerate",
                    "peft": "peft",
                    "unsloth": "unsloth",
                    "unsloth_zoo": "unsloth_zoo",
                    "PIL": "Pillow",
                    "bitsandbytes": "bitsandbytes",
                    "huggingface_hub": "huggingface-hub",
                    "sentencepiece": "sentencepiece",
                    "safetensors": "safetensors",
                }

                def installed_version(package_name: str) -> str | None:
                    try:
                        return importlib.metadata.version(package_name)
                    except importlib.metadata.PackageNotFoundError:
                        return None

                def pip_install(requirements_text: str, constraints_text: str) -> None:
                    subprocess.run([sys.executable, "-m", "pip", "install", "-U", "pip"], check=True)
                    install_root = WORK_ROOT / "_embedded_requirements"
                    install_root.mkdir(parents=True, exist_ok=True)
                    requirements_path = install_root / "requirements.txt"
                    constraints_path = install_root / "constraints.txt"
                    requirements_path.write_text(requirements_text, encoding="utf-8")
                    constraints_path.write_text(constraints_text, encoding="utf-8")
                    subprocess.run(
                        [
                            sys.executable,
                            "-m",
                            "pip",
                            "install",
                            "-r",
                            str(requirements_path),
                            "-c",
                            str(constraints_path),
                        ],
                        check=True,
                    )

                need_install = STRICT_REPO_PINNED_SYNC
                if not need_install:
                    for module_name, package_name in REQUIRED_MODULE_TO_PACKAGE.items():
                        if installed_version(package_name) is None:
                            need_install = True
                            break

                if INSTALL_MODE == "repo_pinned" and need_install:
                    pip_install(EMBEDDED_REQUIREMENTS_TEXT, EMBEDDED_CONSTRAINTS_TEXT)
                elif INSTALL_MODE == "unsloth_auto" and need_install:
                    subprocess.run(
                        "wget -qO- https://raw.githubusercontent.com/unslothai/unsloth/main/unsloth/_auto_install.py | python -",
                        shell=True,
                        check=True,
                    )
                    pip_install(EMBEDDED_REQUIREMENTS_TEXT, EMBEDDED_CONSTRAINTS_TEXT)

                summary = {name: installed_version(name) for name in [
                    "unsloth",
                    "unsloth_zoo",
                    "torch",
                    "transformers",
                    "trl",
                    "datasets",
                    "accelerate",
                    "peft",
                    "bitsandbytes",
                    "huggingface-hub",
                    "sentencepiece",
                    "safetensors",
                ]}
                print(json.dumps(summary, indent=2))
                """
            ),
        }
    )
    cells.append(
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": _src(
                """
                from __future__ import annotations

                import json
                import math
                import os
                import platform
                import random
                import sys
                from collections import Counter
                from datetime import datetime, timezone
                from pathlib import Path
                from typing import Any

                import datasets
                import transformers
                import torch
                import yaml
                from datasets import load_dataset
                from huggingface_hub import hf_hub_download, login
                import huggingface_hub
                from peft import AutoPeftModelForCausalLM
                from PIL import Image
                from transformers import AutoModelForCausalLM, AutoProcessor, AutoTokenizer
                from trl import DPOConfig, DPOTrainer, SFTConfig, SFTTrainer
                from unsloth import FastLanguageModel, FastVisionModel
                from unsloth.trainer import UnslothVisionDataCollator

                EMBEDDED_RUNTIME_DIR = WORK_ROOT / "_embedded_runtime"
                EMBEDDED_RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
                EMBEDDED_RUNTIME_PATH = EMBEDDED_RUNTIME_DIR / "colab_standalone.py"
                EMBEDDED_RUNTIME_PATH.write_text(EMBEDDED_RUNTIME_SOURCE, encoding="utf-8")
                if str(EMBEDDED_RUNTIME_DIR) not in sys.path:
                    sys.path.insert(0, str(EMBEDDED_RUNTIME_DIR))

                from colab_standalone import (
                    MULTIMODAL_SOURCES,
                    TEXT_ONLY_SOURCES,
                    approximate_row_text,
                    build_multimodal_row_from_record,
                    build_text_row_from_record,
                    extract_preference_triplet,
                    materialize_identity_placeholder_assets,
                    render_prompt_messages_to_text,
                    sha256_file,
                )

                CONFIG_ROOT = WORK_ROOT / "embedded_configs"
                CONFIG_ROOT.mkdir(parents=True, exist_ok=True)
                for name, text in EMBEDDED_CONFIG_TEXT.items():
                    (CONFIG_ROOT / name).write_text(text, encoding="utf-8")

                def load_embedded_config(name: str) -> dict[str, Any]:
                    payload = yaml.safe_load(EMBEDDED_CONFIG_TEXT[name]) or {}
                    if not isinstance(payload, dict):
                        raise ValueError(f"embedded config did not parse as mapping: {name}")
                    return payload

                DATASET_MIXTURE = load_embedded_config("dataset_mixture.yaml")
                ALLOWLIST_CFG = load_embedded_config("dataset_sources_allowlist.yaml")
                TRAIN_SFT_CFG = load_embedded_config("train_sft.yaml")
                TRAIN_DPO_CFG = load_embedded_config("train_dpo.yaml")
                RUN_PROFILES_CFG = load_embedded_config("run_profiles.yaml")
                CHAT_TEMPLATE_POLICY = load_embedded_config("chat_template_policy.yaml")
                ALLOWLIST_MAP = {
                    str(source.get("source_id")): source
                    for source in ALLOWLIST_CFG.get("sources", [])
                    if isinstance(source, dict) and source.get("source_id")
                }

                REPORTS = WORK_ROOT / "workspace" / "reports"
                INTERIM = WORK_ROOT / "workspace" / "interim"
                FINAL = WORK_ROOT / "workspace" / "final"
                RUNS_ROOT = WORK_ROOT / "workspace" / "runs"
                ASSET_ROOT = WORK_ROOT / "workspace" / "assets"
                for path in (REPORTS, INTERIM, FINAL, RUNS_ROOT, ASSET_ROOT):
                    path.mkdir(parents=True, exist_ok=True)

                DEFAULT_SFT_NAMES = ["sft_dataset.jsonl", "identity_sft.jsonl"]
                DEFAULT_PREFERENCE_NAMES = ["preference_dataset.jsonl", "identity_preferences.jsonl"]

                def save_json(path: Path, payload: dict[str, Any] | list[Any]) -> None:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

                def iter_jsonl(path: Path):
                    with path.open("r", encoding="utf-8") as handle:
                        for line in handle:
                            stripped = line.strip()
                            if not stripped:
                                continue
                            yield json.loads(stripped)

                def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    with path.open("w", encoding="utf-8") as handle:
                        for row in rows:
                            handle.write(json.dumps(row, ensure_ascii=False) + "\\n")

                def build_run_plan(prefix: str) -> dict[str, Path | str]:
                    safe = "-".join(part for part in prefix.lower().replace("_", "-").split("-") if part) or "colab-main"
                    return {
                        "sft_run_id": f"{safe}-sft",
                        "dpo_run_id": f"{safe}-dpo",
                        "export_run_id": f"{safe}-export",
                        "eval_run_id": f"{safe}-eval",
                        "sft_output_dir": RUNS_ROOT / f"{safe}-sft" / "artifacts" / "sft_model",
                        "sft_checkpoint_dir": RUNS_ROOT / f"{safe}-sft" / "artifacts" / "sft_model" / "checkpoints",
                        "dpo_output_dir": RUNS_ROOT / f"{safe}-dpo" / "artifacts" / "dpo_model",
                        "gguf_dir": RUNS_ROOT / f"{safe}-export" / "artifacts" / "gguf",
                    }

                RUN_PLAN = build_run_plan(PIPELINE_PREFIX)
                SFT_RUN_ID = str(RUN_PLAN["sft_run_id"])
                DPO_RUN_ID = str(RUN_PLAN["dpo_run_id"])
                EXPORT_RUN_ID = str(RUN_PLAN["export_run_id"])
                EVAL_RUN_ID = str(RUN_PLAN["eval_run_id"])

                def create_run_evidence_tree(run_id: str) -> dict[str, Path]:
                    root = RUNS_ROOT / run_id
                    tree = {
                        "root": root,
                        "config_snapshot": root / "config_snapshot",
                        "commands": root / "commands",
                        "environment": root / "environment",
                        "logs": root / "logs",
                        "reports": root / "reports",
                        "artifacts": root / "artifacts",
                        "checksums": root / "checksums",
                    }
                    for path in tree.values():
                        path.mkdir(parents=True, exist_ok=True)
                    return tree

                def write_run_status(run_id: str, *, stage: str, status: str, details: dict[str, Any] | None = None) -> None:
                    payload = {
                        "run_id": run_id,
                        "stage": stage,
                        "status": status,
                        "updated_utc": datetime.now(timezone.utc).isoformat(),
                        "details": details or {},
                    }
                    save_json(RUNS_ROOT / run_id / "STATUS.json", payload)

                def write_run_summary(run_id: str, summary_markdown: str) -> None:
                    path = RUNS_ROOT / run_id / "SUMMARY.md"
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(summary_markdown, encoding="utf-8")

                def resolve_profile_name(requested: str, gpu_total_memory_gb: float | None) -> str:
                    profiles = RUN_PROFILES_CFG.get("profiles") or {}
                    if requested and requested != "auto":
                        if requested not in profiles:
                            raise ValueError(f"unknown profile: {requested}")
                        return requested
                    if gpu_total_memory_gb is not None and gpu_total_memory_gb >= 80 and "default_96gb" in profiles:
                        return "default_96gb"
                    if "safe_fallback" in profiles:
                        return "safe_fallback"
                    return next(iter(profiles))

                def detect_model_artifact_layout(model_dir: str | Path) -> str:
                    path = Path(model_dir)
                    if (path / "adapter_config.json").exists():
                        return "peft_adapter"
                    if (path / "config.json").exists():
                        return "transformers_model"
                    return "unknown"

                def load_text_tokenizer(model_dir: str | Path, *, fallback_model_name: str) -> AutoTokenizer:
                    try:
                        return AutoTokenizer.from_pretrained(str(model_dir), trust_remote_code=True)
                    except Exception:
                        return AutoTokenizer.from_pretrained(fallback_model_name, trust_remote_code=True)

                def load_processor(model_dir: str | Path, *, fallback_model_name: str) -> Any:
                    try:
                        return AutoProcessor.from_pretrained(str(model_dir), trust_remote_code=True)
                    except Exception:
                        return AutoProcessor.from_pretrained(fallback_model_name, trust_remote_code=True)

                def save_processing_assets(processing_class: Any, destination: str | Path) -> None:
                    if hasattr(processing_class, "save_pretrained"):
                        processing_class.save_pretrained(str(destination))

                def detect_gguf_files(path: str | Path) -> list[str]:
                    root = Path(path)
                    if not root.exists():
                        return []
                    return sorted(str(item) for item in root.rglob("*.gguf"))

                def validate_required_variants(files: list[str]) -> dict[str, bool]:
                    lowered = [Path(item).name.lower() for item in files]
                    return {
                        "has_q8_0": any("q8_0" in name for name in lowered),
                        "has_q4_candidate": any("q4" in name for name in lowered),
                    }

                def normalize_for_overlap(text: str) -> set[str]:
                    return {token for token in "".join(ch.lower() if ch.isalnum() else " " for ch in text).split() if token}

                def lexical_overlap(actual: str, expected: str) -> float:
                    a = normalize_for_overlap(actual)
                    b = normalize_for_overlap(expected)
                    if not a or not b:
                        return 0.0
                    return len(a & b) / max(len(b), 1)

                def assess_eval_export_status(results: dict[str, Any], *, run_eval: bool, run_export: bool) -> dict[str, Any]:
                    blocking: list[str] = []
                    if run_eval:
                        if results["checks"].get("identity_correctness", {}).get("status") != "pass":
                            blocking.append(f"identity_correctness:{results['checks'].get('identity_correctness', {}).get('status')}")
                        mm_status = results["checks"].get("multimodal_correctness", {}).get("status")
                        if mm_status not in {"pass", "not_applicable"}:
                            blocking.append(f"multimodal_correctness:{mm_status}")
                    if run_export:
                        export_status = results.get("export_smoke", {}).get("status")
                        if export_status not in {"pass", "structural_only", "skipped"}:
                            blocking.append(f"export_smoke:{export_status}")
                    return {
                        "status": "completed" if not blocking else "needs_review",
                        "blocking_reasons": blocking,
                    }

                def estimate_row_tokens(tokenizer: AutoTokenizer, row: dict[str, Any]) -> int:
                    text = approximate_row_text(row)
                    token_count = len(tokenizer.encode(text, add_special_tokens=False))
                    image_count = sum(
                        1
                        for message in row.get("messages", [])
                        if isinstance(message, dict)
                        for block in (message.get("content") if isinstance(message.get("content"), list) else [])
                        if isinstance(block, dict) and block.get("type") == "image"
                    )
                    return max(token_count + image_count * 256, 1)

                def source_license(source_id: str) -> str:
                    entry = ALLOWLIST_MAP.get(source_id) or {}
                    return str(entry.get("license") or "")

                def resolve_identity_paths() -> dict[str, Path]:
                    for sft_name in DEFAULT_SFT_NAMES:
                        sft_path = IDENTITY_INPUT_DIR / sft_name
                        if sft_path.exists():
                            break
                    else:
                        raise FileNotFoundError(f"Missing identity SFT file in {IDENTITY_INPUT_DIR}; accepted names: {DEFAULT_SFT_NAMES}")
                    for pref_name in DEFAULT_PREFERENCE_NAMES:
                        pref_path = IDENTITY_INPUT_DIR / pref_name
                        if pref_path.exists():
                            break
                    else:
                        raise FileNotFoundError(f"Missing identity preference file in {IDENTITY_INPUT_DIR}; accepted names: {DEFAULT_PREFERENCE_NAMES}")
                    return {"sft": sft_path, "preferences": pref_path}

                def ensure_identity_inputs() -> dict[str, Any]:
                    IDENTITY_INPUT_DIR.mkdir(parents=True, exist_ok=True)
                    try:
                        resolved = resolve_identity_paths()
                        return {
                            "status": "present",
                            "repo_id": IDENTITY_HF_REPO_ID,
                            "identity_paths": {key: str(value) for key, value in resolved.items()},
                        }
                    except FileNotFoundError as initial_error:
                        if not IDENTITY_AUTO_DOWNLOAD:
                            raise
                        download_report = {
                            "status": "downloaded",
                            "repo_id": IDENTITY_HF_REPO_ID,
                            "downloaded_files": [],
                            "initial_error": str(initial_error),
                        }
                        for filename in ("sft_dataset.jsonl", "preference_dataset.jsonl"):
                            downloaded_path = hf_hub_download(
                                repo_id=IDENTITY_HF_REPO_ID,
                                repo_type="dataset",
                                filename=filename,
                                local_dir=str(IDENTITY_INPUT_DIR),
                                local_dir_use_symlinks=False,
                                token=HF_TOKEN,
                            )
                            download_report["downloaded_files"].append(str(downloaded_path))
                        resolved = resolve_identity_paths()
                        download_report["identity_paths"] = {key: str(value) for key, value in resolved.items()}
                        return download_report

                def build_preference_row(source_id: str, record: dict[str, Any], row_id: str) -> dict[str, Any] | None:
                    triplet = extract_preference_triplet(record)
                    if triplet is None:
                        return None
                    prompt, chosen, rejected = triplet
                    return {
                        "id": row_id,
                        "source_id": source_id,
                        "license": source_license(source_id),
                        "thinking": "off",
                        "chat_template_kwargs": {"enable_thinking": False},
                        "prompt": prompt,
                        "prompt_messages": [{"role": "user", "content": prompt}],
                        "chosen": chosen,
                        "rejected": rejected,
                    }

                def collect_multimodal_eval_sample(row: dict[str, Any]) -> dict[str, Any] | None:
                    user_prompt = ""
                    image_path = None
                    expected = ""
                    for message in row.get("messages", []):
                        if not isinstance(message, dict):
                            continue
                        content = message.get("content")
                        if message.get("role") == "user" and isinstance(content, list):
                            for block in content:
                                if isinstance(block, dict) and block.get("type") == "text" and not user_prompt:
                                    user_prompt = str(block.get("text") or "")
                                if isinstance(block, dict) and block.get("type") == "image":
                                    image_path = block.get("image_path") or block.get("path") or block.get("image")
                        if message.get("role") == "assistant" and isinstance(content, list):
                            for block in content:
                                if isinstance(block, dict) and block.get("type") == "text" and not expected:
                                    expected = str(block.get("text") or "")
                    if user_prompt and image_path and expected:
                        return {
                            "prompt": user_prompt,
                            "image_path": str(image_path),
                            "expected_answer": expected,
                            "source_id": row.get("source_id"),
                        }
                    return None

                if HF_TOKEN:
                    login(token=HF_TOKEN)

                print(json.dumps({
                    "embedded_runtime_path": str(EMBEDDED_RUNTIME_PATH),
                    "embedded_config_root": str(CONFIG_ROOT),
                    "work_root": str(WORK_ROOT),
                }, indent=2))
                """
            ),
        }
    )
    cells.append(
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": _src(
                """
                from __future__ import annotations

                import json
                import platform
                import subprocess
                import sys
                from datetime import datetime, timezone

                gpu_devices = [
                    {
                        "index": idx,
                        "name": torch.cuda.get_device_name(idx),
                        "total_memory_gb": round(torch.cuda.get_device_properties(idx).total_memory / (1024**3), 2),
                    }
                    for idx in range(torch.cuda.device_count())
                ] if torch.cuda.is_available() else []
                gpu_total_memory_gb = max((device["total_memory_gb"] for device in gpu_devices), default=None)
                PROFILE = resolve_profile_name(PROFILE, gpu_total_memory_gb)

                base_model_name = TRAIN_SFT_CFG["model"]["base_model"]
                chat_template_driver = load_processor(base_model_name, fallback_model_name=base_model_name)
                tokenizer = load_text_tokenizer(base_model_name, fallback_model_name=base_model_name)
                probe_render = chat_template_driver.apply_chat_template(
                    [{"role": "user", "content": "Say hello in one short sentence."}],
                    tokenize=False,
                    add_generation_prompt=True,
                    enable_thinking=False,
                )
                if "<think>" in probe_render or "</think>" in probe_render:
                    raise RuntimeError("Qwen non-thinking probe failed during env setup")

                env_report = {
                    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                    "python": sys.version,
                    "platform": platform.platform(),
                    "cuda_available": torch.cuda.is_available(),
                    "gpu_devices": gpu_devices,
                    "gpu_total_memory_gb": gpu_total_memory_gb,
                    "resolved_profile": PROFILE,
                    "torch": torch.__version__,
                    "transformers": transformers.__version__,
                    "datasets": datasets.__version__,
                    "huggingface_hub": huggingface_hub.__version__,
                    "base_model": base_model_name,
                    "chat_template_probe": probe_render[:200],
                }
                save_json(REPORTS / "env_sanity.json", env_report)
                freeze = subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True)
                (REPORTS / "env_freeze.txt").write_text(freeze, encoding="utf-8")

                identity_bootstrap = ensure_identity_inputs()
                save_json(REPORTS / "identity_download.json", identity_bootstrap)
                identity_paths = resolve_identity_paths()
                raw_identity_rows = list(iter_jsonl(identity_paths["sft"]))
                raw_identity_prefs = list(iter_jsonl(identity_paths["preferences"]))
                materialized_identity_rows, materialized_identity_assets = materialize_identity_placeholder_assets(
                    raw_identity_rows,
                    ASSET_ROOT / "identity_surrogates",
                )
                materialized_identity_path = INTERIM / "identity_sft_materialized.jsonl"
                write_jsonl(materialized_identity_path, materialized_identity_rows)

                identity_token_total = sum(estimate_row_tokens(tokenizer, row) for row in materialized_identity_rows)
                identity_multimodal_rows = sum(1 for row in materialized_identity_rows if row.get("modality") == "image_text")
                identity_report = {
                    "identity_paths": {k: str(v) for k, v in identity_paths.items()},
                    "identity_bootstrap": identity_bootstrap,
                    "counts": {
                        "sft_rows": len(raw_identity_rows),
                        "preference_rows": len(raw_identity_prefs),
                    },
                    "tokens": {
                        "sft_tokens_total": identity_token_total,
                    },
                    "modality": {
                        "image_text_rows": identity_multimodal_rows,
                        "text_rows": len(materialized_identity_rows) - identity_multimodal_rows,
                    },
                    "materialized_identity_assets": materialized_identity_assets,
                    "materialized_identity_sft": str(materialized_identity_path),
                }
                save_json(REPORTS / "identity_validation.json", identity_report)
                save_json(REPORTS / "identity_asset_materialization.json", materialized_identity_assets)
                print(json.dumps({"env": env_report, "identity": identity_report}, indent=2))
                """
            ),
        }
    )
    cells.append(
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": _src(
                """
                from __future__ import annotations

                import json
                import uuid
                from collections import Counter

                mixture_sources = [source for source in DATASET_MIXTURE.get("sources", []) if isinstance(source, dict)]
                preference_enabled_sources = set(DATASET_MIXTURE.get("preferences", {}).get("enabled_sources", []))
                identity_share_target = float(DATASET_MIXTURE.get("identity_pack", {}).get("fixed_share_of_final_sft_tokens", 0.20))
                open_token_budget_target = int(identity_report["tokens"]["sft_tokens_total"] * ((1.0 - identity_share_target) / identity_share_target))
                if DRY_RUN:
                    open_token_budget_target = min(open_token_budget_target, int(DATASET_MIXTURE.get("token_budgets", {}).get("open_sft_budget", {}).get("dry_run_tokens", 50000)))

                open_sft_rows: list[dict[str, Any]] = []
                open_preference_rows: list[dict[str, Any]] = []
                multimodal_eval_samples: list[dict[str, Any]] = []
                source_reports: list[dict[str, Any]] = []
                global_tokens = 0

                for source_cfg in mixture_sources:
                    source_id = str(source_cfg.get("source_id") or "")
                    if not source_id:
                        continue
                    allow_entry = ALLOWLIST_MAP.get(source_id)
                    if not isinstance(allow_entry, dict) or allow_entry.get("enabled") is not True:
                        source_reports.append({"source_id": source_id, "skipped": "disabled_or_missing_allowlist"})
                        continue
                    if source_id == "HuggingFaceM4/the_cauldron":
                        source_reports.append({"source_id": source_id, "skipped": "subset_allowlist_not_embedded"})
                        continue
                    split = str(allow_entry.get("default_split") or "train")
                    subset = allow_entry.get("subset") if isinstance(allow_entry.get("subset"), str) else None
                    source_budget = int(source_cfg.get("token_budget") or allow_entry.get("max_tokens_cap") or 0)
                    if DRY_RUN:
                        source_budget = min(source_budget, 12000)
                    rows_scanned = 0
                    kept_rows = 0
                    kept_pref_rows = 0
                    kept_tokens = 0
                    multimodal_rows = 0
                    drop_reasons = Counter()

                    try:
                        dataset = load_dataset(source_id, subset, split=split, streaming=STREAMING)
                    except Exception as exc:
                        source_reports.append({"source_id": source_id, "error": str(exc)})
                        continue

                    for record in dataset:
                        if source_budget <= 0 or global_tokens >= open_token_budget_target:
                            break
                        rows_scanned += 1
                        record_id = str(record.get("id") or f"{source_id.replace('/', '_')}-{rows_scanned:08d}" or uuid.uuid4())
                        if str(source_cfg.get("modality")) == "image_text":
                            row = build_multimodal_row_from_record(
                                source_id,
                                record,
                                asset_root=ASSET_ROOT / "open_multimodal",
                                row_id=record_id,
                            )
                        else:
                            row = build_text_row_from_record(
                                source_id,
                                record,
                                row_id=record_id,
                                license_name=source_license(source_id),
                                category=str(source_cfg.get("category") or "utility_tasks"),
                            )
                        if row is None:
                            drop_reasons["unmapped_record"] += 1
                            if DRY_RUN and rows_scanned >= 1000:
                                break
                            continue

                        row_tokens = estimate_row_tokens(tokenizer, row)
                        if row_tokens > source_budget:
                            drop_reasons["source_budget_skip"] += 1
                            continue
                        if global_tokens + row_tokens > open_token_budget_target and not DRY_RUN:
                            drop_reasons["global_budget_skip"] += 1
                            continue

                        open_sft_rows.append(row)
                        kept_rows += 1
                        kept_tokens += row_tokens
                        source_budget -= row_tokens
                        global_tokens += row_tokens
                        if row.get("modality") == "image_text":
                            multimodal_rows += 1
                            if len(multimodal_eval_samples) < 12:
                                sample = collect_multimodal_eval_sample(row)
                                if sample is not None:
                                    multimodal_eval_samples.append(sample)

                        if source_id in preference_enabled_sources:
                            pref_row = build_preference_row(source_id, record, f"{record_id}-pref")
                            if pref_row is not None:
                                open_preference_rows.append(pref_row)
                                kept_pref_rows += 1

                        if DRY_RUN and kept_rows >= 64:
                            break

                    source_reports.append({
                        "source_id": source_id,
                        "split": split,
                        "subset": subset,
                        "rows_scanned": rows_scanned,
                        "kept_rows": kept_rows,
                        "kept_preference_rows": kept_pref_rows,
                        "kept_tokens": kept_tokens,
                        "multimodal_rows": multimodal_rows,
                        "drop_reasons": dict(drop_reasons),
                    })

                open_sft_path = INTERIM / "open_sft.jsonl"
                open_preferences_path = INTERIM / "open_preferences.jsonl"
                write_jsonl(open_sft_path, open_sft_rows)
                write_jsonl(open_preferences_path, open_preference_rows)
                save_json(REPORTS / "eval_multimodal_prompts.json", multimodal_eval_samples)

                open_report = {
                    "source_mode": SOURCE_MODE,
                    "dry_run": DRY_RUN,
                    "streaming": STREAMING,
                    "open_target_tokens": open_token_budget_target,
                    "open_tokens_built": global_tokens,
                    "open_sft_rows": len(open_sft_rows),
                    "open_preference_rows": len(open_preference_rows),
                    "multimodal_eval_samples": len(multimodal_eval_samples),
                    "sources": source_reports,
                    "outputs": {
                        "open_sft": str(open_sft_path),
                        "open_preferences": str(open_preferences_path),
                    },
                }
                save_json(REPORTS / "open_corpus_build_report.json", open_report)
                if not open_sft_rows:
                    raise RuntimeError("Open corpus build produced zero SFT rows")
                if not DRY_RUN and not any(row.get("modality") == "image_text" for row in open_sft_rows):
                    raise RuntimeError("Open corpus build produced no concrete multimodal rows")
                print(json.dumps(open_report, indent=2))
                """
            ),
        }
    )
    cells.append(
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": _src(
                """
                from __future__ import annotations

                import json

                def normalize_identity_preference_row(row: dict[str, Any], idx: int) -> dict[str, Any]:
                    prompt = str(row.get("prompt") or render_prompt_messages_to_text(row.get("prompt_messages")) or "")
                    if not prompt:
                        prompt = "No prompt provided"
                    return {
                        "id": str(row.get("id") or f"identity-pref-{idx:08d}"),
                        "source_id": str(row.get("source_id") or row.get("source") or "identity_pack"),
                        "license": str(row.get("license") or "unknown"),
                        "thinking": "off",
                        "chat_template_kwargs": {"enable_thinking": False},
                        "prompt": prompt,
                        "prompt_messages": row.get("prompt_messages") or [{"role": "user", "content": prompt}],
                        "chosen": str(row.get("chosen") or ""),
                        "rejected": str(row.get("rejected") or ""),
                    }

                identity_rows = list(iter_jsonl(materialized_identity_path))
                open_rows = list(iter_jsonl(open_sft_path))
                identity_preferences = [normalize_identity_preference_row(row, idx) for idx, row in enumerate(raw_identity_prefs, start=1)]
                open_preferences = list(iter_jsonl(open_preferences_path))

                open_target_tokens = int(identity_report["tokens"]["sft_tokens_total"] * ((1.0 - identity_share_target) / identity_share_target))
                selected_open_rows: list[dict[str, Any]] = []
                selected_open_tokens = 0
                for row in open_rows:
                    row_tokens = estimate_row_tokens(tokenizer, row)
                    if selected_open_tokens + row_tokens <= open_target_tokens:
                        selected_open_rows.append(row)
                        selected_open_tokens += row_tokens

                selection_mode = "exact_underfill"
                if selected_open_tokens < open_target_tokens:
                    remaining_candidates = [row for row in open_rows if row not in selected_open_rows]
                    if remaining_candidates:
                        closest = min(
                            remaining_candidates,
                            key=lambda row: abs(open_target_tokens - (selected_open_tokens + estimate_row_tokens(tokenizer, row))),
                        )
                        selected_open_rows.append(closest)
                        selected_open_tokens += estimate_row_tokens(tokenizer, closest)
                        selection_mode = "approximate_closest"

                full_sft_rows = identity_rows + selected_open_rows
                full_preference_rows = identity_preferences + open_preferences
                full_sft_path = FINAL / "full_sft.jsonl"
                full_preferences_path = FINAL / "full_preferences.jsonl"
                write_jsonl(full_sft_path, full_sft_rows)
                write_jsonl(full_preferences_path, full_preference_rows)

                category_hist = Counter(str(row.get("category") or "unknown") for row in full_sft_rows)
                source_hist = Counter(str(row.get("source_id") or "unknown") for row in full_sft_rows)
                modality_hist = Counter(str(row.get("modality") or "text") for row in full_sft_rows)
                token_totals = Counter()
                placeholder_image_block_count = 0
                missing_image_paths = 0
                for row in full_sft_rows:
                    row_tokens = estimate_row_tokens(tokenizer, row)
                    token_totals["total"] += row_tokens
                    token_totals[str(row.get("category") or "unknown")] += row_tokens
                    token_totals[str(row.get("modality") or "text")] += row_tokens
                    for message in row.get("messages", []):
                        content = message.get("content")
                        if isinstance(content, list):
                            for block in content:
                                if isinstance(block, dict) and block.get("type") == "image":
                                    if isinstance(block.get("image"), str):
                                        placeholder_image_block_count += 1
                                    image_path = block.get("image_path")
                                    if image_path and not Path(str(image_path)).exists():
                                        missing_image_paths += 1

                identity_tokens = sum(estimate_row_tokens(tokenizer, row) for row in identity_rows)
                full_tokens = token_totals["total"]
                actual_identity_share = identity_tokens / max(full_tokens, 1)
                validation_report = {
                    "input": {
                        "full_sft": str(full_sft_path),
                        "full_preferences": str(full_preferences_path),
                        "sha256": {
                            "full_sft": sha256_file(full_sft_path),
                            "full_preferences": sha256_file(full_preferences_path),
                        },
                    },
                    "counts": {
                        "sft_rows_total": len(full_sft_rows),
                        "preferences_rows_total": len(full_preference_rows),
                        "identity_sft_rows": len(identity_rows),
                        "identity_preference_rows": len(identity_preferences),
                        "sft_tokens_total": full_tokens,
                        "identity_sft_tokens": identity_tokens,
                        "open_sft_tokens": selected_open_tokens,
                    },
                    "histograms": {
                        "category": dict(category_hist),
                        "modality": dict(modality_hist),
                        "source": dict(source_hist),
                    },
                    "shares": {
                        "token_weighted": {
                            "identity_token_share": actual_identity_share,
                            "modality": {key: value / max(full_tokens, 1) for key, value in token_totals.items() if key in {"text", "image_text"}},
                        },
                    },
                    "targets": {
                        "identity_token_share": identity_share_target,
                        "modality": DATASET_MIXTURE.get("targets", {}).get("modality_share", {}),
                    },
                    "validations": {
                        "preferences_nonempty": len(full_preference_rows) > 0,
                        "placeholder_image_block_count_zero": placeholder_image_block_count == 0,
                        "missing_image_paths_zero": missing_image_paths == 0,
                        "has_multimodal_rows": modality_hist.get("image_text", 0) > 0,
                        "identity_share_close": abs(actual_identity_share - identity_share_target) <= (0.03 if ALLOW_SMALL_SAMPLE else 0.02),
                    },
                    "selection": {
                        "mode": selection_mode,
                        "required_open_tokens_exact": open_target_tokens,
                        "open_tokens_selected": selected_open_tokens,
                    },
                }
                validation_report["pass"] = all(validation_report["validations"].values())
                save_json(REPORTS / "full_dataset_validation.json", validation_report)
                save_json(REPORTS / "mixture_math.json", validation_report["selection"])

                manifest = {
                    "schema_version": "3.0-draft",
                    "created_utc": datetime.now(timezone.utc).isoformat(),
                    "paths": {
                        "full_sft": str(full_sft_path),
                        "full_preferences": str(full_preferences_path),
                        "validation_report": str(REPORTS / "full_dataset_validation.json"),
                    },
                    "sha256": validation_report["input"]["sha256"],
                    "counts": validation_report["counts"],
                    "shares": validation_report["shares"],
                    "targets": validation_report["targets"],
                    "validations": validation_report["validations"],
                }
                save_json(FINAL / "dataset_manifest.json", manifest)
                if not validation_report["pass"]:
                    raise RuntimeError("Full dataset validation failed: " + json.dumps(validation_report["validations"], indent=2))
                print(json.dumps(validation_report, indent=2))
                """
            ),
        }
    )
    cells.append(
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": _src(
                """
                from __future__ import annotations

                import json
                import platform
                import sys

                SFT_OUTPUT_DIR = Path(RUN_PLAN["sft_output_dir"])
                SFT_CHECKPOINT_DIR = Path(RUN_PLAN["sft_checkpoint_dir"])
                sft_training = dict(TRAIN_SFT_CFG.get("training") or {})
                if FIRST_50_STEPS_SANITY:
                    sft_training["max_steps"] = int(TRAIN_SFT_CFG.get("sanity_run", {}).get("max_steps", 50))
                profile_sft = ((RUN_PROFILES_CFG.get("profiles") or {}).get(PROFILE) or {}).get("sft") or {}
                sft_training.update(profile_sft)
                max_seq_length = int(sft_training.get("max_seq_length") or 4096)
                load_in_4bit = bool(TRAIN_SFT_CFG.get("model", {}).get("load_in_4bit", False) or PROFILE == "safe_fallback")

                sft_resolved = {
                    "run_id": SFT_RUN_ID,
                    "profile": PROFILE,
                    "model": TRAIN_SFT_CFG.get("model"),
                    "lora": TRAIN_SFT_CFG.get("lora"),
                    "training": sft_training,
                    "dataset_path": str(full_sft_path),
                    "output_dir": str(SFT_OUTPUT_DIR),
                    "checkpoint_dir": str(SFT_CHECKPOINT_DIR),
                    "chat_template_policy": CHAT_TEMPLATE_POLICY,
                }
                save_json(REPORTS / "train_sft_config_resolved.json", sft_resolved)

                sft_surface = {
                    "dataset_path": str(full_sft_path),
                    "row_count": len(full_sft_rows),
                    "text_rows": sum(1 for row in full_sft_rows if row.get("modality") == "text"),
                    "image_text_rows": sum(1 for row in full_sft_rows if row.get("modality") == "image_text"),
                    "placeholder_image_blocks": validation_report["validations"].get("placeholder_image_block_count_zero") is False,
                }
                save_json(REPORTS / "sft_training_surface.json", sft_surface)

                if not RUN_SFT:
                    print(json.dumps({"status": "skipped", "reason": "RUN_SFT is False"}, indent=2))
                else:
                    run_paths = create_run_evidence_tree(SFT_RUN_ID)
                    save_json(run_paths["config_snapshot"] / "train_sft_resolved.json", sft_resolved)
                    save_json(run_paths["reports"] / "sft_training_surface.json", sft_surface)
                    (run_paths["commands"] / "notebook_90_sft_invocation.txt").write_text(
                        f"profile={PROFILE}\\ndataset={full_sft_path}\\noutput_dir={SFT_OUTPUT_DIR}\\n", encoding="utf-8"
                    )
                    save_json(run_paths["environment"] / "runtime.json", {
                        "python": sys.version,
                        "platform": platform.platform(),
                        "cwd": str(WORK_ROOT),
                    })
                    write_run_status(SFT_RUN_ID, stage="sft", status="running", details=sft_resolved)

                    use_vision_path = sft_surface["image_text_rows"] > 0
                    if use_vision_path:
                        model, processor = FastVisionModel.from_pretrained(
                            model_name=TRAIN_SFT_CFG["model"]["base_model"],
                            max_seq_length=max_seq_length,
                            load_in_4bit=load_in_4bit,
                            dtype=torch.bfloat16,
                            trust_remote_code=True,
                        )
                        model = FastVisionModel.get_peft_model(
                            model,
                            finetune_vision_layers=True,
                            finetune_language_layers=True,
                            finetune_attention_modules=True,
                            finetune_mlp_modules=True,
                            r=int(TRAIN_SFT_CFG["lora"]["r"]),
                            lora_alpha=int(TRAIN_SFT_CFG["lora"]["lora_alpha"]),
                            lora_dropout=float(TRAIN_SFT_CFG["lora"]["lora_dropout"]),
                            bias=str(TRAIN_SFT_CFG["lora"]["bias"]),
                            use_gradient_checkpointing="unsloth",
                            random_state=3407,
                        )
                        FastVisionModel.for_training(model)
                        train_dataset = load_dataset("json", data_files=str(full_sft_path), split="train")
                        trainer = SFTTrainer(
                            model=model,
                            processing_class=processor,
                            data_collator=UnslothVisionDataCollator(model, processor),
                            train_dataset=train_dataset,
                            args=SFTConfig(
                                **sft_training,
                                output_dir=str(SFT_OUTPUT_DIR),
                                max_length=max_seq_length,
                                remove_unused_columns=False,
                                dataset_text_field="",
                                dataset_kwargs={"skip_prepare_dataset": True},
                            ),
                        )
                        dataset_mode = "fastvision_multimodal"
                    else:
                        model, tokenizer = FastLanguageModel.from_pretrained(
                            model_name=TRAIN_SFT_CFG["model"]["base_model"],
                            max_seq_length=max_seq_length,
                            load_in_4bit=load_in_4bit,
                            dtype=torch.bfloat16,
                            trust_remote_code=True,
                        )
                        model = FastLanguageModel.get_peft_model(
                            model,
                            r=int(TRAIN_SFT_CFG["lora"]["r"]),
                            lora_alpha=int(TRAIN_SFT_CFG["lora"]["lora_alpha"]),
                            lora_dropout=float(TRAIN_SFT_CFG["lora"]["lora_dropout"]),
                            target_modules=TRAIN_SFT_CFG["lora"]["target_modules"],
                            bias=str(TRAIN_SFT_CFG["lora"]["bias"]),
                        )
                        raw_dataset = load_dataset("json", data_files=str(full_sft_path), split="train")
                        def render_text(example: dict[str, Any]) -> dict[str, str]:
                            rendered = tokenizer.apply_chat_template(example["messages"], tokenize=False, add_generation_prompt=False, enable_thinking=False)
                            return {"text": rendered}
                        train_dataset = raw_dataset.map(render_text, remove_columns=raw_dataset.column_names)
                        trainer = SFTTrainer(
                            model=model,
                            processing_class=tokenizer,
                            train_dataset=train_dataset,
                            args=SFTConfig(**sft_training, output_dir=str(SFT_OUTPUT_DIR), max_length=max_seq_length),
                            dataset_text_field="text",
                        )
                        dataset_mode = "fastlanguage_text_only"

                    train_result = trainer.train()
                    trainer.save_model(str(SFT_OUTPUT_DIR))
                    save_processing_assets(processor if use_vision_path else tokenizer, SFT_OUTPUT_DIR)
                    artifact_checksums = {
                        str(path.relative_to(SFT_OUTPUT_DIR)): sha256_file(path)
                        for path in sorted(SFT_OUTPUT_DIR.rglob("*"))
                        if path.is_file()
                    }
                    report = {
                        "run_id": SFT_RUN_ID,
                        "dataset_mode": dataset_mode,
                        "metrics": getattr(train_result, "metrics", {}),
                        "artifact_files": sorted(artifact_checksums),
                        "use_vision_path": use_vision_path,
                    }
                    save_json(run_paths["reports"] / "sft_training.json", report)
                    save_json(run_paths["checksums"] / "artifacts.json", artifact_checksums)
                    write_run_status(SFT_RUN_ID, stage="sft", status="completed", details=report)
                    write_run_summary(SFT_RUN_ID, f"# SFT Summary\\n\\n```json\\n{json.dumps(report, indent=2)}\\n```")
                    print(json.dumps(report, indent=2))
                """
            ),
        }
    )
    cells.append(
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": _src(
                """
                from __future__ import annotations

                import json
                import platform
                import sys

                DPO_OUTPUT_DIR = Path(RUN_PLAN["dpo_output_dir"])
                dpo_training = dict(TRAIN_DPO_CFG.get("training") or {})
                profile_dpo = ((RUN_PROFILES_CFG.get("profiles") or {}).get(PROFILE) or {}).get("dpo") or {}
                dpo_training.update(profile_dpo)
                dpo_resolved = {
                    "run_id": DPO_RUN_ID,
                    "profile": PROFILE,
                    "model": TRAIN_DPO_CFG.get("model"),
                    "lora": TRAIN_DPO_CFG.get("lora"),
                    "training": dpo_training,
                    "dpo": TRAIN_DPO_CFG.get("dpo"),
                    "preferences": TRAIN_DPO_CFG.get("preferences"),
                    "output_dir": str(DPO_OUTPUT_DIR),
                    "sft_checkpoint_or_adapter": str(SFT_OUTPUT_DIR),
                }
                save_json(REPORTS / "train_dpo_config_resolved.json", dpo_resolved)

                DPO_COMPLETED = False
                DPO_REPORT = {"status": "skipped", "reason": "RUN_DPO is False"}

                if not RUN_DPO:
                    print(json.dumps({"status": "skipped", "reason": "RUN_DPO is False"}, indent=2))
                else:
                    if not SFT_OUTPUT_DIR.exists():
                        raise FileNotFoundError(f"missing SFT output dir: {SFT_OUTPUT_DIR}")
                    run_paths = create_run_evidence_tree(DPO_RUN_ID)
                    save_json(run_paths["config_snapshot"] / "train_dpo_resolved.json", dpo_resolved)
                    (run_paths["commands"] / "notebook_90_dpo_invocation.txt").write_text(
                        f"profile={PROFILE}\\npreferences={full_preferences_path}\\noutput_dir={DPO_OUTPUT_DIR}\\n", encoding="utf-8"
                    )
                    save_json(run_paths["environment"] / "runtime.json", {
                        "python": sys.version,
                        "platform": platform.platform(),
                        "cwd": str(WORK_ROOT),
                    })
                    write_run_status(DPO_RUN_ID, stage="dpo", status="running", details=dpo_resolved)

                    sft_layout = detect_model_artifact_layout(SFT_OUTPUT_DIR)
                    dpo_loader_mode = None
                    try:
                        dataset = load_dataset("json", data_files=str(full_preferences_path), split="train")
                        if sft_layout == "peft_adapter":
                            model = AutoPeftModelForCausalLM.from_pretrained(
                                str(SFT_OUTPUT_DIR),
                                torch_dtype=torch.bfloat16,
                                trust_remote_code=True,
                                is_trainable=True,
                            )
                            dpo_loader_mode = "AutoPeftModelForCausalLM"
                        else:
                            model = AutoModelForCausalLM.from_pretrained(
                                str(SFT_OUTPUT_DIR),
                                torch_dtype=torch.bfloat16,
                                trust_remote_code=True,
                            )
                            dpo_loader_mode = "AutoModelForCausalLM"
                        tokenizer = load_text_tokenizer(SFT_OUTPUT_DIR, fallback_model_name=TRAIN_DPO_CFG["model"]["base_model"])
                        if tokenizer.pad_token is None:
                            tokenizer.pad_token = tokenizer.eos_token
                        tokenizer.padding_side = "right"

                        def format_prompt(example: dict[str, Any]) -> dict[str, Any]:
                            prompt = str(example.get("prompt") or "").strip()
                            if not prompt:
                                prompt = render_prompt_messages_to_text(example.get("prompt_messages"))
                            if not prompt:
                                raise RuntimeError("Preference row missing prompt or prompt_messages")
                            rendered_prompt = tokenizer.apply_chat_template(
                                [{"role": "user", "content": prompt}],
                                tokenize=False,
                                add_generation_prompt=True,
                                enable_thinking=False,
                            )
                            return {"prompt": rendered_prompt}

                        dataset = dataset.map(format_prompt)
                        trainer = DPOTrainer(
                            model=model,
                            ref_model=None,
                            processing_class=tokenizer,
                            train_dataset=dataset,
                            args=DPOConfig(**dpo_training, output_dir=str(DPO_OUTPUT_DIR)),
                            beta=float(TRAIN_DPO_CFG.get("dpo", {}).get("beta", 0.1)),
                        )
                        train_result = trainer.train()
                        trainer.save_model(str(DPO_OUTPUT_DIR))
                        tokenizer.save_pretrained(str(DPO_OUTPUT_DIR))
                        try:
                            processor = load_processor(SFT_OUTPUT_DIR, fallback_model_name=TRAIN_DPO_CFG["model"]["base_model"])
                            save_processing_assets(processor, DPO_OUTPUT_DIR)
                        except Exception:
                            pass
                        artifact_checksums = {
                            str(path.relative_to(DPO_OUTPUT_DIR)): sha256_file(path)
                            for path in sorted(DPO_OUTPUT_DIR.rglob("*"))
                            if path.is_file()
                        }
                        report = {
                            "run_id": DPO_RUN_ID,
                            "status": "completed",
                            "metrics": getattr(train_result, "metrics", {}),
                            "artifact_files": sorted(artifact_checksums),
                            "sft_model_layout": sft_layout,
                            "loader_mode": dpo_loader_mode,
                        }
                        DPO_COMPLETED = True
                        DPO_REPORT = report
                        save_json(run_paths["reports"] / "dpo_training.json", report)
                        save_json(run_paths["checksums"] / "artifacts.json", artifact_checksums)
                        write_run_status(DPO_RUN_ID, stage="dpo", status="completed", details=report)
                        write_run_summary(DPO_RUN_ID, f"# DPO Summary\\n\\n```json\\n{json.dumps(report, indent=2)}\\n```")
                        print(json.dumps(report, indent=2))
                    except Exception as exc:
                        DPO_REPORT = {
                            "run_id": DPO_RUN_ID,
                            "status": "failed",
                            "error": str(exc),
                            "sft_model_layout": sft_layout,
                            "loader_mode": dpo_loader_mode,
                            "fallback_final_model_dir": str(SFT_OUTPUT_DIR),
                        }
                        save_json(run_paths["reports"] / "dpo_training.json", DPO_REPORT)
                        write_run_status(DPO_RUN_ID, stage="dpo", status="failed", details=DPO_REPORT)
                        write_run_summary(DPO_RUN_ID, f"# DPO Summary\\n\\n```json\\n{json.dumps(DPO_REPORT, indent=2)}\\n```")
                        print(json.dumps(DPO_REPORT, indent=2))
                """
            ),
        }
    )
    cells.append(
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": _src(
                """
                from __future__ import annotations

                import json
                import platform
                import sys

                FINAL_MODEL_DIR = DPO_OUTPUT_DIR if DPO_COMPLETED else SFT_OUTPUT_DIR
                GGUF_DIR = Path(RUN_PLAN["gguf_dir"])
                GGUF_EXPORT_REPORT = {"status": "skipped", "reason": "RUN_EXPORT is False"}

                if RUN_EXPORT:
                    if not FINAL_MODEL_DIR.exists():
                        raise FileNotFoundError(f"final model dir missing for export: {FINAL_MODEL_DIR}")
                    run_paths = create_run_evidence_tree(EXPORT_RUN_ID)
                    MERGED_DIR = run_paths["artifacts"] / "merged_16bit"
                    GGUF_DIR = run_paths["artifacts"] / "gguf"
                    MERGED_DIR.mkdir(parents=True, exist_ok=True)
                    GGUF_DIR.mkdir(parents=True, exist_ok=True)
                    final_model_layout = detect_model_artifact_layout(FINAL_MODEL_DIR)
                    export_input_dir = FINAL_MODEL_DIR
                    export_base_model = TRAIN_DPO_CFG["model"]["base_model"] if RUN_DPO else TRAIN_SFT_CFG["model"]["base_model"]
                    merge_mode = None
                    merge_error = None
                    if final_model_layout == "peft_adapter":
                        merge_attempt_errors = []
                        for merge_loader_name, merge_loader in (("FastVisionModel", FastVisionModel), ("FastLanguageModel", FastLanguageModel)):
                            try:
                                merge_model, merge_processing_class = merge_loader.from_pretrained(
                                    model_name=str(FINAL_MODEL_DIR),
                                    max_seq_length=4096,
                                    load_in_4bit=False,
                                    dtype=torch.bfloat16,
                                    trust_remote_code=True,
                                )
                                merge_model.save_pretrained_merged(
                                    str(MERGED_DIR),
                                    merge_processing_class,
                                    save_method="merged_16bit",
                                )
                                save_processing_assets(merge_processing_class, MERGED_DIR)
                                export_input_dir = MERGED_DIR
                                merge_mode = f"{merge_loader_name}.save_pretrained_merged"
                                break
                            except Exception as exc:
                                merge_attempt_errors.append(f"{merge_loader_name}: {exc}")
                        if export_input_dir == FINAL_MODEL_DIR:
                            try:
                                merge_tokenizer = load_text_tokenizer(FINAL_MODEL_DIR, fallback_model_name=export_base_model)
                                merged_model = AutoPeftModelForCausalLM.from_pretrained(
                                    str(FINAL_MODEL_DIR),
                                    torch_dtype=torch.bfloat16,
                                    trust_remote_code=True,
                                )
                                merged_model = merged_model.merge_and_unload()
                                merged_model.save_pretrained(str(MERGED_DIR))
                                merge_tokenizer.save_pretrained(str(MERGED_DIR))
                                try:
                                    merge_processor = load_processor(FINAL_MODEL_DIR, fallback_model_name=export_base_model)
                                    save_processing_assets(merge_processor, MERGED_DIR)
                                except Exception:
                                    pass
                                export_input_dir = MERGED_DIR
                                merge_mode = "AutoPeftModelForCausalLM.merge_and_unload"
                            except Exception as exc:
                                merge_attempt_errors.append(f"AutoPeftModelForCausalLM: {exc}")
                                merge_error = " | ".join(merge_attempt_errors)

                    save_json(run_paths["config_snapshot"] / "export_inputs.json", {
                        "run_id": EXPORT_RUN_ID,
                        "final_model_dir": str(FINAL_MODEL_DIR),
                        "final_model_layout": final_model_layout,
                        "export_input_dir": str(export_input_dir),
                        "gguf_quantization_methods": GGUF_QUANTIZATION_METHODS,
                        "merge_mode": merge_mode,
                    })
                    (run_paths["commands"] / "notebook_90_export_invocation.txt").write_text(
                        f"final_model_dir={FINAL_MODEL_DIR}\\nexport_input_dir={export_input_dir}\\ngguf_dir={GGUF_DIR}\\n", encoding="utf-8"
                    )
                    save_json(run_paths["environment"] / "runtime.json", {
                        "python": sys.version,
                        "platform": platform.platform(),
                        "cwd": str(WORK_ROOT),
                    })
                    write_run_status(EXPORT_RUN_ID, stage="export", status="running")

                    export_mode = None
                    direct_errors = []
                    export_candidates = []
                    if export_input_dir.exists():
                        export_candidates.append(export_input_dir)
                    if FINAL_MODEL_DIR.exists() and FINAL_MODEL_DIR not in export_candidates:
                        export_candidates.append(FINAL_MODEL_DIR)
                    for candidate_dir in export_candidates:
                        for loader_name, loader in (("FastVisionModel", FastVisionModel), ("FastLanguageModel", FastLanguageModel)):
                            try:
                                model, tokenizer = loader.from_pretrained(
                                    model_name=str(candidate_dir),
                                    max_seq_length=4096,
                                    load_in_4bit=False,
                                    dtype=torch.bfloat16,
                                    trust_remote_code=True,
                                )
                                model.save_pretrained_gguf(
                                    str(GGUF_DIR),
                                    tokenizer,
                                    quantization_method=GGUF_QUANTIZATION_METHODS,
                                )
                                export_mode = f"{loader_name}.save_pretrained_gguf:{candidate_dir}"
                                break
                            except Exception as exc:
                                direct_errors.append(f"{loader_name}@{candidate_dir}: {exc}")
                        if export_mode is not None:
                            break

                    gguf_files = detect_gguf_files(GGUF_DIR)
                    variants = validate_required_variants(gguf_files)
                    GGUF_EXPORT_REPORT = {
                        "run_id": EXPORT_RUN_ID,
                        "final_model_dir": str(FINAL_MODEL_DIR),
                        "final_model_layout": final_model_layout,
                        "export_input_dir": str(export_input_dir),
                        "gguf_dir": str(GGUF_DIR),
                        "merged_dir": str(MERGED_DIR),
                        "merge_mode": merge_mode,
                        "export_mode": export_mode,
                        "gguf_files": gguf_files,
                        "variants": variants,
                        "direct_errors": direct_errors,
                        "merge_error": merge_error,
                    }
                    save_json(run_paths["reports"] / "gguf_export.json", GGUF_EXPORT_REPORT)
                    save_json(run_paths["checksums"] / "artifacts.json", {
                        "gguf_export_report": sha256_file(run_paths["reports"] / "gguf_export.json"),
                        "gguf_artifacts": {
                            str(path.relative_to(GGUF_DIR)): sha256_file(path)
                            for path in sorted(GGUF_DIR.rglob("*"))
                            if path.is_file()
                        },
                    })
                    if not (variants["has_q8_0"] and variants["has_q4_candidate"]):
                        write_run_status(EXPORT_RUN_ID, stage="export", status="failed", details=GGUF_EXPORT_REPORT)
                        raise RuntimeError("GGUF export did not produce the required q8_0 and q4 variants")
                    write_run_status(EXPORT_RUN_ID, stage="export", status="completed", details=GGUF_EXPORT_REPORT)
                    write_run_summary(EXPORT_RUN_ID, f"# GGUF Export Summary\\n\\n```json\\n{json.dumps(GGUF_EXPORT_REPORT, indent=2)}\\n```")
                    print(json.dumps(GGUF_EXPORT_REPORT, indent=2))
                else:
                    print(json.dumps(GGUF_EXPORT_REPORT, indent=2))
                """
            ),
        }
    )
    cells.append(
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": _src(
                """
                from __future__ import annotations

                import json
                import platform
                import sys

                final_model_dir = DPO_OUTPUT_DIR if DPO_COMPLETED else SFT_OUTPUT_DIR
                final_model_layout = detect_model_artifact_layout(final_model_dir)
                results = {
                    "run_eval": RUN_EVAL,
                    "run_export": RUN_EXPORT,
                    "run_id": EVAL_RUN_ID,
                    "final_model_dir": str(final_model_dir),
                    "final_model_layout": final_model_layout,
                    "dpo_report": DPO_REPORT,
                    "checks": {
                        "identity_correctness": {"status": "skipped"},
                        "self_branding_rate": {"status": "skipped"},
                        "vision_hallucination_on_no_image": {"status": "skipped"},
                        "multimodal_correctness": {"status": "skipped"},
                    },
                }

                if RUN_EVAL or RUN_EXPORT:
                    run_paths = create_run_evidence_tree(EVAL_RUN_ID)
                    save_json(run_paths["config_snapshot"] / "eval_export_inputs.json", {
                        "model_dir": str(final_model_dir),
                        "model_layout": final_model_layout,
                        "gguf_dir": str(GGUF_DIR),
                        "run_eval": RUN_EVAL,
                        "run_export": RUN_EXPORT,
                    })
                    (run_paths["commands"] / "notebook_90_eval_invocation.txt").write_text(
                        f"run_eval={RUN_EVAL}\\nrun_export={RUN_EXPORT}\\nmodel_dir={final_model_dir}\\ngguf_dir={GGUF_DIR}\\n",
                        encoding="utf-8",
                    )
                    save_json(run_paths["environment"] / "runtime.json", {
                        "python": sys.version,
                        "platform": platform.platform(),
                        "cwd": str(WORK_ROOT),
                    })
                    write_run_status(EVAL_RUN_ID, stage="eval_export", status="running")

                    if RUN_EVAL:
                        text_loader_mode = None
                        text_loader_error = None
                        try:
                            if final_model_layout == "peft_adapter":
                                text_model = AutoPeftModelForCausalLM.from_pretrained(
                                    str(final_model_dir),
                                    torch_dtype=torch.bfloat16,
                                    trust_remote_code=True,
                                )
                                text_loader_mode = "AutoPeftModelForCausalLM"
                            else:
                                text_model = AutoModelForCausalLM.from_pretrained(
                                    str(final_model_dir),
                                    torch_dtype=torch.bfloat16,
                                    trust_remote_code=True,
                                )
                                text_loader_mode = "AutoModelForCausalLM"
                            text_tokenizer = load_text_tokenizer(final_model_dir, fallback_model_name=TRAIN_DPO_CFG["model"]["base_model"] if DPO_COMPLETED else TRAIN_SFT_CFG["model"]["base_model"])
                            if text_tokenizer.pad_token is None:
                                text_tokenizer.pad_token = text_tokenizer.eos_token
                            text_model.eval()

                            def render_prompt(prompt: str) -> str:
                                rendered = text_tokenizer.apply_chat_template(
                                    [{"role": "user", "content": prompt}],
                                    tokenize=False,
                                    add_generation_prompt=True,
                                    enable_thinking=False,
                                )
                                if "<think>" in rendered or "</think>" in rendered:
                                    raise RuntimeError("Rendered eval prompt still contains thinking markers")
                                return rendered

                            def generate_text(prompt: str, max_new_tokens: int = 96) -> str:
                                rendered = render_prompt(prompt)
                                toks = text_tokenizer(rendered, return_tensors="pt")
                                toks = {key: value.to(text_model.device) for key, value in toks.items()}
                                with torch.no_grad():
                                    out = text_model.generate(
                                        **toks,
                                        max_new_tokens=max_new_tokens,
                                        do_sample=EVAL_DO_SAMPLE,
                                        temperature=EVAL_TEMPERATURE if EVAL_DO_SAMPLE else None,
                                        top_p=EVAL_TOP_P if EVAL_DO_SAMPLE else None,
                                        top_k=EVAL_TOP_K if EVAL_DO_SAMPLE else None,
                                        pad_token_id=text_tokenizer.pad_token_id,
                                        eos_token_id=text_tokenizer.eos_token_id,
                                    )
                                generated = out[0][toks["input_ids"].shape[-1]:]
                                return text_tokenizer.decode(generated, skip_special_tokens=True).strip()
                        except Exception as exc:
                            text_loader_error = str(exc)
                            text_model, text_processor = FastVisionModel.from_pretrained(
                                model_name=str(final_model_dir),
                                max_seq_length=4096,
                                load_in_4bit=False,
                                dtype=torch.bfloat16,
                                trust_remote_code=True,
                            )
                            FastVisionModel.for_inference(text_model)
                            text_loader_mode = "FastVisionModel"

                            def render_prompt(prompt: str) -> str:
                                rendered = text_processor.apply_chat_template(
                                    [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
                                    add_generation_prompt=True,
                                    enable_thinking=False,
                                )
                                if "<think>" in rendered or "</think>" in rendered:
                                    raise RuntimeError("Rendered eval prompt still contains thinking markers")
                                return rendered

                            def generate_text(prompt: str, max_new_tokens: int = 96) -> str:
                                rendered = render_prompt(prompt)
                                toks = text_processor(text=rendered, return_tensors="pt")
                                toks = {key: value.to(text_model.device) for key, value in toks.items()}
                                with torch.no_grad():
                                    out = text_model.generate(
                                        **toks,
                                        max_new_tokens=max_new_tokens,
                                        do_sample=EVAL_DO_SAMPLE,
                                        temperature=EVAL_TEMPERATURE if EVAL_DO_SAMPLE else None,
                                        top_p=EVAL_TOP_P if EVAL_DO_SAMPLE else None,
                                        top_k=EVAL_TOP_K if EVAL_DO_SAMPLE else None,
                                    )
                                generated = out[0][toks["input_ids"].shape[-1]:]
                                decoder = text_processor.tokenizer if hasattr(text_processor, "tokenizer") else text_processor
                                return decoder.decode(generated, skip_special_tokens=True).strip()

                        torch.manual_seed(EVAL_SEED)

                        identity_prompts = ["What is your name?", "Who created you?"]
                        identity_outputs = [generate_text(prompt) for prompt in identity_prompts]
                        identity_ok = all(("Lumis" in output and "Eptesicus" in output) for output in identity_outputs)
                        results["checks"]["identity_correctness"] = {
                            "status": "pass" if identity_ok else "fail",
                            "outputs": identity_outputs,
                            "loader_mode": text_loader_mode,
                            "loader_fallback_error": text_loader_error,
                        }

                        neutral_prompts = [
                            "Summarize this paragraph in one sentence.",
                            "Rewrite this sentence in simpler English.",
                            "What is the water cycle?",
                        ]
                        neutral_outputs = [generate_text(prompt) for prompt in neutral_prompts]
                        brand_hits = sum(1 for text in neutral_outputs if "Lumis" in text or "Eptesicus" in text)
                        results["checks"]["self_branding_rate"] = {
                            "status": "pass",
                            "rate": brand_hits / max(len(neutral_outputs), 1),
                            "outputs": neutral_outputs,
                            "loader_mode": text_loader_mode,
                        }

                        no_image_prompts = ["Describe the image.", "What objects are visible here?"]
                        no_image_outputs = [generate_text(prompt) for prompt in no_image_prompts]
                        hallucination_hits = sum(
                            1
                            for text in no_image_outputs
                            if "cannot" not in text.lower() and "can't" not in text.lower() and "no image" not in text.lower()
                        )
                        results["checks"]["vision_hallucination_on_no_image"] = {
                            "status": "pass" if hallucination_hits == 0 else "warn",
                            "hallucination_hits": hallucination_hits,
                            "outputs": no_image_outputs,
                            "loader_mode": text_loader_mode,
                        }

                        eval_mm_path = REPORTS / "eval_multimodal_prompts.json"
                        if eval_mm_path.exists():
                            mm_items = json.loads(eval_mm_path.read_text(encoding="utf-8"))
                            if mm_items:
                                vision_model_dir = MERGED_DIR if RUN_EXPORT and 'MERGED_DIR' in globals() and MERGED_DIR.exists() else final_model_dir
                                try:
                                    vision_model, vision_processor = FastVisionModel.from_pretrained(
                                        model_name=str(vision_model_dir),
                                        max_seq_length=4096,
                                        load_in_4bit=False,
                                        dtype=torch.bfloat16,
                                        trust_remote_code=True,
                                    )
                                    FastVisionModel.for_inference(vision_model)
                                    overlaps = []
                                    outputs = []
                                    for item in mm_items[:6]:
                                        image = Image.open(item["image_path"]).convert("RGB")
                                        messages = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": item["prompt"]}]}]
                                        input_text = vision_processor.apply_chat_template(messages, add_generation_prompt=True, enable_thinking=False)
                                        inputs = vision_processor(images=image, text=input_text, add_special_tokens=False, return_tensors="pt").to("cuda")
                                        with torch.no_grad():
                                            generated = vision_model.generate(**inputs, max_new_tokens=96, use_cache=True)
                                        decoder = vision_processor.tokenizer if hasattr(vision_processor, "tokenizer") else vision_processor
                                        answer = decoder.decode(generated[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True).strip()
                                        outputs.append(answer)
                                        overlaps.append(lexical_overlap(answer, item["expected_answer"]))
                                    average_overlap = sum(overlaps) / max(len(overlaps), 1)
                                    results["checks"]["multimodal_correctness"] = {
                                        "status": "pass" if average_overlap >= 0.10 else "fail",
                                        "items_evaluated": len(overlaps),
                                        "average_overlap": average_overlap,
                                        "outputs": outputs,
                                    }
                                except Exception as exc:
                                    results["checks"]["multimodal_correctness"] = {
                                        "status": "skipped",
                                        "reason": "vision_eval_loader_failed",
                                        "error": str(exc),
                                    }
                            else:
                                results["checks"]["multimodal_correctness"] = {
                                    "status": "not_applicable",
                                    "reason": "multimodal_eval_samples_empty",
                                }
                        else:
                            results["checks"]["multimodal_correctness"] = {
                                "status": "not_applicable",
                                "reason": "multimodal_eval_samples_missing",
                            }

                    if RUN_EXPORT and GGUF_DIR.exists():
                        gguf_files = detect_gguf_files(GGUF_DIR)
                        variants = validate_required_variants(gguf_files)
                        results["export_smoke"] = {
                            "status": "structural_only" if variants["has_q8_0"] and variants["has_q4_candidate"] else "fail",
                            "gguf_files": gguf_files,
                            "variants": variants,
                        }
                    else:
                        results["export_smoke"] = {
                            "status": "skipped",
                            "reason": "GGUF export disabled or directory missing",
                        }

                    save_json(REPORTS / "export_smoke.json", results)
                    save_json(run_paths["reports"] / "export_smoke.json", results)
                    save_json(run_paths["checksums"] / "artifacts.json", {
                        "export_smoke_report": sha256_file(REPORTS / "export_smoke.json"),
                        "gguf_artifacts": {
                            str(path.relative_to(GGUF_DIR)): sha256_file(path)
                            for path in sorted(GGUF_DIR.rglob("*"))
                            if path.is_file()
                        } if GGUF_DIR.exists() else {},
                    })
                    assessment = assess_eval_export_status(results, run_eval=RUN_EVAL, run_export=RUN_EXPORT)
                    results["run_status_assessment"] = assessment
                    write_run_status(EVAL_RUN_ID, stage="eval_export", status=assessment["status"], details=results)
                    write_run_summary(EVAL_RUN_ID, f"# Eval / Export Summary\\n\\n```json\\n{json.dumps(results, indent=2)}\\n```")
                    print(json.dumps(results, indent=2))
                else:
                    print(json.dumps(results, indent=2))
                """
            ),
        }
    )
    cells.append(
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": _src(
                """
                from __future__ import annotations

                import json
                import shutil
                import sys

                export_root = EXPORT_PERSIST_ROOT / PIPELINE_PREFIX
                if export_root.exists():
                    shutil.rmtree(export_root)
                export_root.mkdir(parents=True, exist_ok=True)

                copied = {}
                for name, source in {
                    "reports": REPORTS,
                    "final": FINAL,
                    "runs": RUNS_ROOT,
                    "assets": ASSET_ROOT,
                }.items():
                    if source.exists():
                        destination = export_root / name
                        shutil.copytree(source, destination, dirs_exist_ok=True)
                        copied[name] = str(destination)

                gguf_candidates = detect_gguf_files(GGUF_DIR) if GGUF_DIR.exists() else []
                summary = {
                    "export_root": str(export_root),
                    "copied": copied,
                    "gguf_candidates": gguf_candidates,
                }
                print(json.dumps(summary, indent=2))

                if DOWNLOAD_GGUF_TO_BROWSER and gguf_candidates and "google.colab" in sys.modules:
                    from google.colab import files  # type: ignore
                    chosen = next(
                        (path for path in gguf_candidates if DOWNLOAD_GGUF_VARIANT_TOKEN.lower() in Path(path).name.lower()),
                        gguf_candidates[0],
                    )
                    print(f"downloading: {chosen}")
                    files.download(chosen)
                """
            ),
        }
    )

    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    _compile_notebook_code_cells(notebook)
    return notebook


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    notebook = build_notebook()
    OUTPUT_PATH.write_text(json.dumps(notebook, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
