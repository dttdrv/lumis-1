from __future__ import annotations

import json
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = REPO_ROOT / "lumis1" / "colab_unified_unsloth_first.py"
NOTEBOOK_SPECS = [
    {
        "filename": "THE NOTEBOOK-sanity.ipynb",
        "title": "THE NOTEBOOK-sanity",
        "status": "Sanity Colab surface",
        "run_sanity_only": True,
    },
    {
        "filename": "THE NOTEBOOK-updated.ipynb",
        "title": "THE NOTEBOOK-updated",
        "status": "Canonical full-run Colab surface",
        "run_sanity_only": False,
    },
]
CONFIG_NAMES = [
    "dataset_mixture.yaml",
    "dataset_sources_allowlist.yaml",
    "train_sft.yaml",
    "train_dpo.yaml",
    "run_profiles.yaml",
]


def _src(text: str) -> list[str]:
    text = textwrap.dedent(text).strip("\n") + "\n"
    return text.splitlines(keepends=True)


def _compile_notebook_code_cells(notebook: dict, output_path: Path) -> None:
    for idx, cell in enumerate(notebook.get("cells", [])):
        if cell.get("cell_type") != "code":
            continue
        source = "".join(cell.get("source", []))
        compile(source, f"{output_path}#cell{idx}", "exec")


def build_notebook(*, filename: str, title: str, status: str, run_sanity_only: bool) -> dict:
    runtime_source = RUNTIME_PATH.read_text(encoding="utf-8")
    embedded_configs = {
        name: (REPO_ROOT / "configs" / name).read_text(encoding="utf-8")
        for name in CONFIG_NAMES
    }
    requirements_text = (REPO_ROOT / "requirements.txt").read_text(encoding="utf-8")
    output_path = REPO_ROOT / filename

    cells: list[dict] = []
    
    def add_markdown(text: str) -> None:
        cells.append(
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": _src(text),
            }
        )

    def add_code(text: str) -> None:
        cells.append(
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": _src(text),
            }
        )

    add_markdown(
        f"""
        # {title}

        Status: {status} | Draft until a real Colab G4 run produces `workspace/runs/<run_id>/`.

        Guarantees:
        1. self-contained runtime bootstrap from embedded helper code and embedded config snapshots
        2. Unsloth-first install path by default, with a matrix-based Unsloth fallback only after the primary path fails
        3. safe Drive mount recovery
        4. automatic identity bootstrap from `STnoui/lumis1-identity`
        5. multimodal SFT as the main training path, not a hidden text-only fallback
        6. GGUF export first from the strongest completed artifact of the current run
        7. automatic browser download of the final artifact or `final_deliverables.zip`

        Non-guarantees:
        1. multimodal DPO is not claimed as stable on this path; the default policy skips it on a multimodal run when only text preferences are available
        2. proof-bearing success still requires a real Colab G4 run tree under `workspace/runs/`
        """
    )

    add_code(
        f"""
        from __future__ import annotations

        import json
        import os
        import platform
        import shutil
        import subprocess
        import sys
        from datetime import datetime, timezone
        from pathlib import Path

        NOTEBOOK_SELF_CONTAINED = True
        WORK_ROOT = Path("/content/lumis1_unified")
        WORKSPACE_ROOT = WORK_ROOT / "workspace"
        REPORTS_ROOT = WORKSPACE_ROOT / "reports"
        FINAL_ROOT = WORKSPACE_ROOT / "final"
        RUNS_ROOT = WORKSPACE_ROOT / "runs"
        ARTIFACTS_ROOT = WORKSPACE_ROOT / "artifacts"
        CHECKSUMS_ROOT = WORKSPACE_ROOT / "checksums"
        REPO_ROOT = Path("/content/lumis1_unified_repo_stub")
        DRIVE_ROOT = Path("/content/drive/MyDrive/lumis1_unified")
        IDENTITY_INPUT_DIR = WORK_ROOT / "identity_input"
        IDENTITY_REPO_ID = os.environ.get("LUMIS1_IDENTITY_HF_REPO", "STnoui/lumis1-identity")
        INSTALL_STRATEGY = "unsloth_first"
        PROFILE = "auto"
        PROFILE_OVERRIDE = os.environ.get("LUMIS1_PROFILE")
        RUN_SANITY_ONLY = {str(run_sanity_only)}
        BASE_MODEL = "Qwen/Qwen3.5-4B"
        EXPORT_QUANTIZATION_METHODS = ["q4_k_m", "q8_0"]
        EXPERIMENTAL_DPO = False
        RUN_ID = datetime.now(timezone.utc).strftime("colab91-%Y%m%dT%H%M%SZ")
        RUN_ROOT = RUNS_ROOT / RUN_ID
        STATUS_PATH = RUN_ROOT / "STATUS.json"
        SUMMARY_PATH = RUN_ROOT / "SUMMARY.md"
        BOOTSTRAP_ROOT = RUN_ROOT / "bootstrap"
        DATASET_RUN_ROOT = RUN_ROOT / "dataset"
        SFT_RUN_ROOT = RUN_ROOT / "sft"
        EXPORT_SFT_RUN_ROOT = RUN_ROOT / "export_sft"
        DPO_RUN_ROOT = RUN_ROOT / "dpo"
        EXPORT_FINAL_RUN_ROOT = RUN_ROOT / "export_final"
        EVAL_RUN_ROOT = RUN_ROOT / "eval"
        RUN_STAGE_DIRS = {{
            "bootstrap": BOOTSTRAP_ROOT,
            "dataset": DATASET_RUN_ROOT,
            "sft": SFT_RUN_ROOT,
            "export_sft": EXPORT_SFT_RUN_ROOT,
            "dpo": DPO_RUN_ROOT,
            "export_final": EXPORT_FINAL_RUN_ROOT,
            "eval": EVAL_RUN_ROOT,
            "artifacts": RUN_ROOT / "artifacts",
            "checksums": RUN_ROOT / "checksums",
        }}
        EMBEDDED_CONFIG_TEXT = {json.dumps(embedded_configs, ensure_ascii=False)}
        EMBEDDED_RUNTIME_SOURCE = {json.dumps(runtime_source, ensure_ascii=False)}
        EMBEDDED_REQUIREMENTS_TEXT = {json.dumps(requirements_text, ensure_ascii=False)}
        OUTPUT_PATH = REPO_ROOT / {json.dumps(filename)}

        for path in [
            WORK_ROOT,
            WORKSPACE_ROOT,
            REPORTS_ROOT / "bootstrap",
            FINAL_ROOT,
            RUNS_ROOT,
            ARTIFACTS_ROOT,
            CHECKSUMS_ROOT,
            *RUN_STAGE_DIRS.values(),
        ]:
            path.mkdir(parents=True, exist_ok=True)

        os.chdir(WORK_ROOT)
        print(json.dumps({{
            "run_id": RUN_ID,
            "work_root": str(WORK_ROOT),
            "workspace_root": str(WORKSPACE_ROOT),
            "run_root": str(RUN_ROOT),
            "install_strategy": INSTALL_STRATEGY,
            "profile": PROFILE,
            "profile_override": PROFILE_OVERRIDE,
            "run_sanity_only": RUN_SANITY_ONLY,
            "base_model": BASE_MODEL,
            "identity_repo_id": IDENTITY_REPO_ID,
        }}, indent=2))
        """
    )

    add_code(
        """
        from __future__ import annotations

        import json
        import os
        import shutil
        import sys
        from pathlib import Path

        IN_COLAB = "google.colab" in sys.modules
        if IN_COLAB:
            from google.colab import drive  # type: ignore

        def write_json(path: Path, payload: object) -> None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\\n", encoding="utf-8")

        def mount_drive_safely(mountpoint: str = "/content/drive") -> dict[str, object]:
            mount_path = Path(mountpoint)
            report = {
                "mountpoint": mountpoint,
                "exists_before": mount_path.exists(),
                "is_mount_before": os.path.ismount(mountpoint),
                "entries_before": [],
                "recovery_action": None,
                "mounted": False,
            }
            if mount_path.exists() and mount_path.is_dir():
                report["entries_before"] = sorted(item.name for item in mount_path.iterdir())[:20]
            if not IN_COLAB:
                report["mounted"] = False
                report["recovery_action"] = "not_running_in_colab"
                return report
            if os.path.ismount(mountpoint):
                report["mounted"] = True
                report["recovery_action"] = "already_mounted"
                return report
            if mount_path.exists():
                if mount_path.is_file() or mount_path.is_symlink():
                    mount_path.unlink()
                    report["recovery_action"] = "removed_file_or_symlink"
                elif mount_path.is_dir() and any(mount_path.iterdir()):
                    shutil.rmtree(mount_path, ignore_errors=True)
                    report["recovery_action"] = "removed_nonempty_directory"
            drive.mount(mountpoint, force_remount=bool(report["recovery_action"]))
            report["mounted"] = os.path.ismount(mountpoint)
            return report

        DRIVE_MOUNT_RESULT = mount_drive_safely("/content/drive")
        write_json(REPORTS_ROOT / "bootstrap" / "drive_mount.json", DRIVE_MOUNT_RESULT)
        write_json(BOOTSTRAP_ROOT / "drive_mount.json", DRIVE_MOUNT_RESULT)
        print(json.dumps(DRIVE_MOUNT_RESULT, indent=2))
        """
    )

    add_code(
        """
        from __future__ import annotations

        import importlib
        import importlib.metadata
        import json
        import os
        import re
        import subprocess
        import sys
        from pathlib import Path

        CORE_UNSLOTH_MANAGED = {
            "torch",
            "transformers",
            "trl",
            "accelerate",
            "peft",
            "bitsandbytes",
            "torchvision",
            "unsloth",
            "unsloth_zoo",
        }

        def _requirement_name(line: str) -> str:
            candidate = line.strip()
            if not candidate or candidate.startswith("#"):
                return ""
            for token in ("[", ">", "=", "<", "!", "~"):
                if token in candidate:
                    candidate = candidate.split(token, 1)[0]
                    break
            return candidate.strip().lower()

        def select_supplemental_requirements(requirements_text: str) -> list[str]:
            selected = []
            seen = set()
            for raw in requirements_text.splitlines():
                name = _requirement_name(raw)
                line = raw.strip()
                if not line or not name or name in CORE_UNSLOTH_MANAGED or name in seen:
                    continue
                selected.append(line)
                seen.add(name)
            return selected

        def package_versions(packages: list[str]) -> dict[str, str | None]:
            report = {}
            for package in packages:
                try:
                    report[package] = importlib.metadata.version(package)
                except importlib.metadata.PackageNotFoundError:
                    report[package] = None
            return report

        def detect_torch_cuda() -> tuple[str, str]:
            try:
                import torch
                cuda_version = getattr(torch.version, "cuda", None) or os.environ.get("CUDA_VERSION") or "12.4"
                return str(torch.__version__), str(cuda_version)
            except Exception:
                return "2.5.0", os.environ.get("CUDA_VERSION", "12.4")

        def build_unsloth_matrix_install_command(torch_version: str, cuda_version: str) -> str:
            match = re.match(r"^(\\d+)\\.(\\d+)", str(torch_version))
            if not match:
                raise ValueError(f"unsupported torch version: {torch_version}")
            major, minor = int(match.group(1)), int(match.group(2))
            if (major, minor) >= (2, 9):
                torch_tag = "torch290"
            elif (major, minor) >= (2, 8):
                torch_tag = "torch280"
            elif (major, minor) >= (2, 7):
                torch_tag = "torch270"
            elif (major, minor) >= (2, 6):
                torch_tag = "torch260"
            elif (major, minor) >= (2, 5):
                torch_tag = "torch250"
            elif (major, minor) >= (2, 4):
                torch_tag = "torch240"
            else:
                raise ValueError(f"unsupported torch version: {torch_version}")
            cuda_text = str(cuda_version).strip().replace(".", "")
            matrix_tag = f"cu{cuda_text}-{torch_tag}"
            return (
                "pip install --upgrade pip && "
                "pip install --no-deps git+https://github.com/unslothai/unsloth-zoo.git#egg=unsloth_zoo && "
                f"pip install \\\"unsloth[{matrix_tag}] @ git+https://github.com/unslothai/unsloth.git\\\" "
                "--no-build-isolation"
            )

        def pip_install(args: list[str]) -> None:
            subprocess.run([sys.executable, "-m", "pip", *args], check=True)

        SUPPLEMENTAL_REQUIREMENTS = select_supplemental_requirements(EMBEDDED_REQUIREMENTS_TEXT)
        install_report = {
            "install_strategy": INSTALL_STRATEGY,
            "supplemental_requirements": SUPPLEMENTAL_REQUIREMENTS,
            "primary_command": [sys.executable, "-m", "pip", "install", "unsloth"],
            "fallback_command": None,
            "used_fallback": False,
        }

        pip_install(["install", "--upgrade", "pip"])
        try:
            pip_install(["install", "unsloth"])
            importlib.import_module("unsloth")
        except Exception:
            torch_version, cuda_version = detect_torch_cuda()
            fallback_command = build_unsloth_matrix_install_command(torch_version, cuda_version)
            install_report["fallback_command"] = fallback_command
            install_report["used_fallback"] = True
            subprocess.run(fallback_command, shell=True, check=True)
            importlib.import_module("unsloth")

        if SUPPLEMENTAL_REQUIREMENTS:
            pip_install(["install", *SUPPLEMENTAL_REQUIREMENTS])

        install_report["versions"] = package_versions([
            "unsloth",
            "unsloth_zoo",
            "torch",
            "transformers",
            "trl",
            "accelerate",
            "peft",
            "bitsandbytes",
            "torchvision",
            "datasets",
            "huggingface-hub",
            "pillow",
        ])
        write_json(REPORTS_ROOT / "bootstrap" / "install_strategy_and_versions.json", install_report)
        write_json(BOOTSTRAP_ROOT / "install_strategy_and_versions.json", install_report)
        print(json.dumps(install_report, indent=2))
        """
    )

    add_code(
        f"""
        from __future__ import annotations

        import importlib
        import json
        import sys
        from pathlib import Path

        EMBEDDED_RUNTIME_DIR = WORK_ROOT / "_embedded_runtime"
        EMBEDDED_RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        EMBEDDED_RUNTIME_PATH = EMBEDDED_RUNTIME_DIR / "colab_unified_unsloth_first.py"
        EMBEDDED_RUNTIME_PATH.write_text(EMBEDDED_RUNTIME_SOURCE, encoding="utf-8")
        if str(EMBEDDED_RUNTIME_DIR) not in sys.path:
            sys.path.insert(0, str(EMBEDDED_RUNTIME_DIR))

        EMBEDDED_CONFIG_DIR = WORK_ROOT / "_embedded_configs"
        EMBEDDED_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        for name, text in EMBEDDED_CONFIG_TEXT.items():
            (EMBEDDED_CONFIG_DIR / name).write_text(text, encoding="utf-8")

        from colab_unified_unsloth_first import (
            IDENTITY_ALLOW_PATTERNS,
            build_multimodal_row_from_record,
            build_text_row_from_record,
            build_zip_bundle,
            choose_final_download_target,
            collect_file_checksums,
            create_final_report_payload,
            extract_preference_triplet,
            materialize_identity_placeholder_assets,
            materialize_processor_ready_sft_rows,
            resolve_sft_model_plan,
            resolve_source_stream_plan,
            resolve_dpo_policy,
            resolve_unsloth_matrix_install_command,
            select_notebook_profile,
            sha256_file,
        )

        import torch
        import yaml
        from datasets import load_dataset
        from huggingface_hub import snapshot_download
        from PIL import Image
        from transformers import AutoProcessor
        from unsloth import FastVisionModel
        from unsloth.trainer import UnslothVisionDataCollator

        DATASET_MIXTURE = yaml.safe_load(EMBEDDED_CONFIG_TEXT["dataset_mixture.yaml"])
        DATASET_ALLOWLIST = yaml.safe_load(EMBEDDED_CONFIG_TEXT["dataset_sources_allowlist.yaml"])
        TRAIN_SFT_CFG = yaml.safe_load(EMBEDDED_CONFIG_TEXT["train_sft.yaml"])
        TRAIN_DPO_CFG = yaml.safe_load(EMBEDDED_CONFIG_TEXT["train_dpo.yaml"])
        RUN_PROFILES = yaml.safe_load(EMBEDDED_CONFIG_TEXT["run_profiles.yaml"])

        if torch.cuda.is_available():
            gpu_props = torch.cuda.get_device_properties(0)
            GPU_RUNTIME = {{
                "name": gpu_props.name,
                "total_memory_gb": round(float(gpu_props.total_memory) / (1024 ** 3), 3),
                "device_count": torch.cuda.device_count(),
            }}
        else:
            GPU_RUNTIME = {{
                "name": "cpu",
                "total_memory_gb": None,
                "device_count": 0,
            }}

        PROFILE = select_notebook_profile(
            RUN_PROFILES,
            profile_override=PROFILE_OVERRIDE,
            gpu_name=GPU_RUNTIME["name"],
            total_memory_gb=GPU_RUNTIME["total_memory_gb"],
        )
        PROFILE_CFG = RUN_PROFILES["profiles"][PROFILE]
        SFT_MAX_STEPS = (
            int(TRAIN_SFT_CFG.get("sanity_run", {{}}).get("max_steps", 50))
            if RUN_SANITY_ONLY
            else int(TRAIN_SFT_CFG["training"]["max_steps"])
        )

        import_report = {{
            "runtime_module": str(EMBEDDED_RUNTIME_PATH),
            "identity_allow_patterns": IDENTITY_ALLOW_PATTERNS,
            "required_imports": ["FastVisionModel", "UnslothVisionDataCollator", "AutoProcessor", "load_dataset", "snapshot_download"],
            "profile": PROFILE,
            "profile_cfg": PROFILE_CFG,
            "gpu_runtime": GPU_RUNTIME,
            "sft_max_steps": SFT_MAX_STEPS,
            "run_sanity_only": RUN_SANITY_ONLY,
        }}
        write_json(BOOTSTRAP_ROOT / "embedded_runtime_imports.json", import_report)
        print(json.dumps(import_report, indent=2))
        """
    )

    add_code(
        """
        from __future__ import annotations

        import json
        from pathlib import Path

        def iter_jsonl(path: Path):
            with path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if line:
                        yield json.loads(line)

        IDENTITY_STAGE_DIR = DATASET_RUN_ROOT / "identity"
        IDENTITY_STAGE_DIR.mkdir(parents=True, exist_ok=True)
        identity_snapshot_dir = snapshot_download(
            repo_id=IDENTITY_REPO_ID,
            repo_type="dataset",
            local_dir=str(IDENTITY_STAGE_DIR),
            allow_patterns=IDENTITY_ALLOW_PATTERNS,
        )
        sft_identity_path = IDENTITY_STAGE_DIR / "sft_dataset.jsonl"
        preference_identity_path = IDENTITY_STAGE_DIR / "preference_dataset.jsonl"
        if not sft_identity_path.exists() or not preference_identity_path.exists():
            raise FileNotFoundError("identity bootstrap failed to produce canonical filenames")
        identity_report = {
            "repo_id": IDENTITY_REPO_ID,
            "snapshot_dir": str(identity_snapshot_dir),
            "sft_path": str(sft_identity_path),
            "preference_path": str(preference_identity_path),
            "sft_rows": sum(1 for _ in iter_jsonl(sft_identity_path)),
            "preference_rows": sum(1 for _ in iter_jsonl(preference_identity_path)),
        }
        write_json(REPORTS_ROOT / "bootstrap" / "identity_download.json", identity_report)
        write_json(BOOTSTRAP_ROOT / "identity_download.json", identity_report)
        print(json.dumps(identity_report, indent=2))
        """
    )

    add_code(
        """
        from __future__ import annotations

        import json
        from collections import Counter
        from pathlib import Path

        OPEN_SFT_PATH = FINAL_ROOT / "full_sft.jsonl"
        OPEN_PREFERENCE_PATH = FINAL_ROOT / "full_preferences.jsonl"
        OPEN_ASSET_ROOT = DATASET_RUN_ROOT / "open_assets"
        OPEN_ASSET_ROOT.mkdir(parents=True, exist_ok=True)
        COLAB_SCAN_CAP = 512
        LOCAL_SCAN_CAP = 2048
        MAX_RECORDS_SCANNED_PER_SOURCE = min(
            int(DATASET_MIXTURE.get("ingestion_defaults", {}).get("max_records_scanned_per_source") or LOCAL_SCAN_CAP),
            COLAB_SCAN_CAP if IN_COLAB else LOCAL_SCAN_CAP,
        )
        MAX_UNMAPPED_ROWS_PER_SOURCE = 256 if IN_COLAB else 768

        def write_jsonl(path: Path, rows: list[dict]) -> None:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8") as handle:
                for row in rows:
                    handle.write(json.dumps(row, ensure_ascii=False) + "\\n")

        def load_jsonl(path: Path) -> list[dict]:
            with path.open("r", encoding="utf-8") as handle:
                return [json.loads(line) for line in handle if line.strip()]

        allowlist_map = {
            item["source_id"]: item
            for item in DATASET_ALLOWLIST.get("sources", [])
            if isinstance(item, dict) and item.get("enabled")
        }
        open_sft_rows = []
        open_preference_rows = []
        source_results = []

        for source_cfg in DATASET_MIXTURE.get("sources", []):
            source_id = source_cfg.get("source_id")
            if source_id not in allowlist_map:
                continue
            source_plan = resolve_source_stream_plan(
                source_id,
                default_split=allowlist_map[source_id].get("default_split", "train"),
                default_subset=allowlist_map[source_id].get("subset")
                if isinstance(allowlist_map[source_id].get("subset"), str)
                else None,
            )
            split_name = source_plan["split"]
            subset_name = source_plan["subset"]
            if source_plan["status"] == "skipped":
                source_results.append({
                    "source_id": source_id,
                    "split": split_name,
                    "subset": subset_name,
                    "accepted": 0,
                    "scanned": 0,
                    "preference_rows": 0,
                    "status": "skipped",
                    "drop_reasons": dict(source_plan["drop_reasons"]),
                })
                continue
            try:
                dataset = load_dataset(source_id, subset_name, split=split_name, streaming=True)
                scanned = 0
                accepted = 0
                preference_rows = 0
                drop_reasons = Counter()
                if source_cfg.get("modality") == "image_text":
                    for record in dataset:
                        if scanned >= MAX_RECORDS_SCANNED_PER_SOURCE:
                            drop_reasons["scan_cap_reached"] += 1
                            break
                        scanned += 1
                        if scanned == 1 or scanned % 64 == 0:
                            print(json.dumps({
                                "source_id": source_id,
                                "split": split_name,
                                "subset": subset_name,
                                "scanned": scanned,
                                "accepted": accepted,
                            }, indent=2))
                        row = build_multimodal_row_from_record(
                            source_id,
                            record,
                            asset_root=OPEN_ASSET_ROOT,
                            row_id=f"{source_id.replace('/', '__')}-{scanned:08d}",
                        )
                        if row is None:
                            drop_reasons["unmapped_record"] += 1
                            if drop_reasons["unmapped_record"] >= MAX_UNMAPPED_ROWS_PER_SOURCE:
                                drop_reasons["unmapped_record_cap_reached"] += 1
                                break
                            continue
                        open_sft_rows.append(row)
                        accepted += 1
                        if accepted >= 8:
                            break
                else:
                    for record in dataset:
                        if scanned >= MAX_RECORDS_SCANNED_PER_SOURCE:
                            drop_reasons["scan_cap_reached"] += 1
                            break
                        scanned += 1
                        if scanned == 1 or scanned % 64 == 0:
                            print(json.dumps({
                                "source_id": source_id,
                                "split": split_name,
                                "subset": subset_name,
                                "scanned": scanned,
                                "accepted": accepted,
                                "preference_rows": preference_rows,
                            }, indent=2))
                        row = build_text_row_from_record(
                            source_id,
                            record,
                            row_id=f"{source_id.replace('/', '__')}-{scanned:08d}",
                            license_name=allowlist_map[source_id].get("license", "unknown"),
                            category=(allowlist_map[source_id].get("category") or ["utility_tasks"])[0],
                        )
                        if row is not None:
                            open_sft_rows.append(row)
                            accepted += 1
                        else:
                            drop_reasons["unmapped_record"] += 1
                            if drop_reasons["unmapped_record"] >= MAX_UNMAPPED_ROWS_PER_SOURCE:
                                drop_reasons["unmapped_record_cap_reached"] += 1
                                break
                        triplet = extract_preference_triplet(record)
                        if triplet is not None and source_id in set(DATASET_MIXTURE.get("preferences", {}).get("enabled_sources", [])):
                            prompt, chosen, rejected = triplet
                            open_preference_rows.append({
                                "id": f"{source_id.replace('/', '__')}-pref-{accepted:08d}",
                                "source_id": source_id,
                                "prompt": prompt,
                                "chosen": chosen,
                                "rejected": rejected,
                            })
                            preference_rows += 1
                        if accepted >= 8 and scanned >= 32:
                            break
                source_results.append({
                    "source_id": source_id,
                    "split": split_name,
                    "subset": subset_name,
                    "accepted": accepted,
                    "scanned": scanned,
                    "preference_rows": preference_rows,
                    "status": "ok",
                    "drop_reasons": dict(drop_reasons),
                })
            except Exception as exc:
                source_results.append({
                    "source_id": source_id,
                    "split": split_name,
                    "subset": subset_name,
                    "accepted": 0,
                    "scanned": 0,
                    "preference_rows": 0,
                    "status": "failed",
                    "error": str(exc),
                })

        identity_sft_rows = load_jsonl(sft_identity_path)
        identity_preference_rows = load_jsonl(preference_identity_path)
        materialized_identity_rows, identity_materialization = materialize_identity_placeholder_assets(
            identity_sft_rows,
            DATASET_RUN_ROOT / "identity_assets",
        )
        merged_sft_rows = materialized_identity_rows + open_sft_rows
        merged_preference_rows = identity_preference_rows + open_preference_rows
        write_jsonl(OPEN_SFT_PATH, merged_sft_rows)
        write_jsonl(OPEN_PREFERENCE_PATH, merged_preference_rows)

        dataset_report = {
            "final_sft_path": str(OPEN_SFT_PATH),
            "final_preferences_path": str(OPEN_PREFERENCE_PATH),
            "identity_sft_rows": len(identity_sft_rows),
            "identity_preference_rows": len(identity_preference_rows),
            "open_sft_rows": len(open_sft_rows),
            "open_preference_rows": len(open_preference_rows),
            "merged_sft_rows": len(merged_sft_rows),
            "merged_preference_rows": len(merged_preference_rows),
            "identity_materialization": identity_materialization,
            "source_results": source_results,
        }
        write_json(DATASET_RUN_ROOT / "dataset_build_report.json", dataset_report)
        print(json.dumps(dataset_report, indent=2))
        """
    )

    add_code(
        """
        from __future__ import annotations

        import json

        with OPEN_SFT_PATH.open("r", encoding="utf-8") as handle:
            merged_sft_rows = [json.loads(line) for line in handle if line.strip()]

        processor_ready_rows = materialize_processor_ready_sft_rows(merged_sft_rows)
        multimodal_rows = [row for row in processor_ready_rows if row.get("images")]
        if not multimodal_rows:
            raise RuntimeError("blocking: merged SFT dataset has zero concrete image rows after materialization")

        processor_ready_report = {
            "processor_ready_rows": len(processor_ready_rows),
            "multimodal_rows": len(multimodal_rows),
            "sample_ids": [row["id"] for row in multimodal_rows[:5]],
        }
        write_json(DATASET_RUN_ROOT / "processor_ready_report.json", processor_ready_report)
        print(json.dumps(processor_ready_report, indent=2))
        """
    )

    add_code(
        """
        from __future__ import annotations

        import json
        import torch
        from datasets import Dataset
        from trl import SFTConfig, SFTTrainer

        SFT_MODEL_DIR = SFT_RUN_ROOT / "artifacts" / "sft_model"
        SFT_MODEL_DIR.mkdir(parents=True, exist_ok=True)
        processor = AutoProcessor.from_pretrained(BASE_MODEL, trust_remote_code=True)
        sft_model_plan = resolve_sft_model_plan(TRAIN_SFT_CFG)
        model, tokenizer = FastVisionModel.from_pretrained(
            model_name=BASE_MODEL,
            load_in_4bit=sft_model_plan["load_in_4bit"],
            trust_remote_code=True,
        )
        if sft_model_plan["lora_enabled"]:
            model = FastVisionModel.get_peft_model(model, **sft_model_plan["peft_kwargs"])
        train_dataset = Dataset.from_list(multimodal_rows)
        trainer = SFTTrainer(
            model=model,
            processing_class=processor,
            data_collator=UnslothVisionDataCollator(model, processor),
            train_dataset=train_dataset,
            args=SFTConfig(
                output_dir=str(SFT_MODEL_DIR),
                per_device_train_batch_size=PROFILE_CFG["sft"]["per_device_train_batch_size"],
                gradient_accumulation_steps=PROFILE_CFG["sft"]["gradient_accumulation_steps"],
                max_steps=SFT_MAX_STEPS,
                logging_steps=int(TRAIN_SFT_CFG["training"]["logging_steps"]),
                save_steps=int(TRAIN_SFT_CFG["training"]["save_steps"]),
                bf16=True,
                max_length=int(PROFILE_CFG["sft"]["max_seq_length"]),
            ),
        )
        trainer.train()
        processor.save_pretrained(str(SFT_MODEL_DIR / "processor"))
        trainer.model.save_pretrained(str(SFT_MODEL_DIR))
        sft_report = {
            "output_dir": str(SFT_MODEL_DIR),
            "rows_used": len(multimodal_rows),
            "base_model": BASE_MODEL,
            "profile": PROFILE,
            "profile_cfg": PROFILE_CFG,
            "load_in_4bit": sft_model_plan["load_in_4bit"],
            "lora_enabled": sft_model_plan["lora_enabled"],
            "max_length": int(PROFILE_CFG["sft"]["max_seq_length"]),
            "max_steps": SFT_MAX_STEPS,
            "run_sanity_only": RUN_SANITY_ONLY,
            "run_training_default": True,
        }
        write_json(SFT_RUN_ROOT / "sft_report.json", sft_report)
        print(json.dumps(sft_report, indent=2))
        """
    )

    add_code(
        """
        from __future__ import annotations

        import json

        EXPORT_SFT_DIR = EXPORT_SFT_RUN_ROOT / "artifacts"
        EXPORT_SFT_DIR.mkdir(parents=True, exist_ok=True)
        GGUF_DIR = EXPORT_SFT_DIR / "gguf"
        GGUF_DIR.mkdir(parents=True, exist_ok=True)
        FINAL_EXPORT_FILES = []

        if hasattr(model, "save_pretrained_gguf"):
            model.save_pretrained_gguf(str(GGUF_DIR), tokenizer, quantization_method=EXPORT_QUANTIZATION_METHODS)

        for path in sorted(GGUF_DIR.rglob("*")):
            if path.is_file():
                FINAL_EXPORT_FILES.append(path)

        if not FINAL_EXPORT_FILES:
            raise RuntimeError("blocking: GGUF export produced no files")

        ZIP_BUNDLE_PATH = EXPORT_SFT_DIR / "final_deliverables.zip"
        build_zip_bundle(ZIP_BUNDLE_PATH, FINAL_EXPORT_FILES)

        export_report = {
            "export_dir": str(EXPORT_SFT_DIR),
            "gguf_dir": str(GGUF_DIR),
            "gguf_files": [str(path) for path in FINAL_EXPORT_FILES],
            "zip_bundle_path": str(ZIP_BUNDLE_PATH),
            "export_quantization_methods": EXPORT_QUANTIZATION_METHODS,
        }
        write_json(EXPORT_SFT_RUN_ROOT / "gguf_export_report.json", export_report)
        print(json.dumps(export_report, indent=2))
        """
    )

    add_code(
        """
        from __future__ import annotations

        import json

        preference_has_images = False
        dpo_policy = resolve_dpo_policy(
            is_multimodal_run=True,
            preference_has_images=preference_has_images,
            experimental_dpo_enabled=EXPERIMENTAL_DPO,
        )
        write_json(DPO_RUN_ROOT / "dpo_policy.json", dpo_policy)
        if dpo_policy["run_dpo"]:
            dpo_result = {"status": "not_implemented_in_default_path", "reason": "experimental_only"}
        else:
            dpo_result = dpo_policy
        write_json(DPO_RUN_ROOT / "dpo_result.json", dpo_result)
        print(json.dumps(dpo_result, indent=2))
        """
    )

    add_code(
        """
        from __future__ import annotations

        import json

        final_export_root = EXPORT_FINAL_RUN_ROOT / "artifacts"
        final_export_root.mkdir(parents=True, exist_ok=True)
        selected_artifact_root = EXPORT_SFT_DIR
        selected_export_files = FINAL_EXPORT_FILES
        selected_zip_path = ZIP_BUNDLE_PATH
        if dpo_policy["run_dpo"] and (DPO_RUN_ROOT / "final_deliverables.zip").exists():
            selected_artifact_root = DPO_RUN_ROOT
            selected_export_files = list((DPO_RUN_ROOT / "artifacts").rglob("*.gguf"))
            selected_zip_path = DPO_RUN_ROOT / "final_deliverables.zip"

        eval_report = {
            "selected_artifact_root": str(selected_artifact_root),
            "selected_export_files": [str(path) for path in selected_export_files],
            "selected_zip_path": str(selected_zip_path),
            "selection_order": "post-DPO export bundle if fully successful, otherwise SFT export bundle",
        }
        write_json(EVAL_RUN_ROOT / "eval_selection_report.json", eval_report)
        print(json.dumps(eval_report, indent=2))
        """
    )

    add_code(
        """
        from __future__ import annotations

        import json
        import shutil
        import sys
        from pathlib import Path

        if not selected_export_files and not Path(selected_zip_path).exists():
            raise RuntimeError("blocking: no final export artifact exists to package or download")

        RUN_ARTIFACTS_DIR = RUN_ROOT / "artifacts"
        RUN_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        mirrored_files = []
        for artifact_path in [Path(path) for path in selected_export_files]:
            if artifact_path.exists():
                destination = RUN_ARTIFACTS_DIR / artifact_path.name
                shutil.copy2(artifact_path, destination)
                mirrored_files.append(destination)
        if Path(selected_zip_path).exists():
            zip_destination = RUN_ARTIFACTS_DIR / Path(selected_zip_path).name
            shutil.copy2(selected_zip_path, zip_destination)
        else:
            zip_destination = RUN_ARTIFACTS_DIR / "final_deliverables.zip"

        final_target = choose_final_download_target(
            final_export_files=mirrored_files,
            zip_bundle_path=zip_destination,
            single_file_size_limit_bytes=1900 * 1024 * 1024,
        )
        final_report = create_final_report_payload(
            what_changed=[
                "Created notebook 91 as the canonical Colab-first surface.",
                "Made Unsloth-first bootstrap the default install strategy.",
                "Embedded runtime helper code and config snapshots into the notebook.",
                "Added HF identity auto-download, safe Drive mount recovery, and automatic final download.",
            ],
            what_was_verified=[
                "Notebook source compiles cell-by-cell during generation.",
                "Helper-layer tests cover install filtering, DPO policy, processor-ready multimodal rows, and final bundle selection.",
                "The notebook records bootstrap reports for drive mount, identity download, and install strategy.",
            ],
            what_remains_unproven=[
                "A real Colab G4 execution for the full multimodal training and GGUF export path.",
                "Whether the current text-only preference surface supports a stable multimodal DPO stage.",
            ],
            highest_risk_unresolved_issue="The first proof-bearing Colab G4 run still needs to confirm that upstream multimodal dataset schemas and surrogate identity images behave acceptably end to end.",
            exact_next_step={json.dumps(f"Run {filename} on a real Colab G4 runtime and inspect the emitted workspace/runs tree for the generated run ID.")},
        )
        final_checksums = collect_file_checksums(RUN_ARTIFACTS_DIR)
        write_json(RUN_ROOT / "checksums" / "artifacts.json", final_checksums)
        write_json(REPORTS_ROOT / "final_run_report.json", final_report)
        (REPORTS_ROOT / "final_run_report.md").write_text(
            "\\n".join([
                "# Final Run Report",
                "",
                "## what_changed",
                *[f"- {item}" for item in final_report["what_changed"]],
                "",
                "## what_was_verified",
                *[f"- {item}" for item in final_report["what_was_verified"]],
                "",
                "## what_remains_unproven",
                *[f"- {item}" for item in final_report["what_remains_unproven"]],
                "",
                "## highest_risk_unresolved_issue",
                final_report["highest_risk_unresolved_issue"],
                "",
                "## exact_next_step",
                final_report["exact_next_step"],
                "",
            ]) + "\\n",
            encoding="utf-8",
        )
        STATUS_PATH.write_text(
            json.dumps({"run_id": RUN_ID, "final_target": str(final_target["download_path"]), "download_mode": final_target["download_mode"]}, indent=2) + "\\n",
            encoding="utf-8",
        )
        SUMMARY_PATH.write_text(
            "# Notebook 91 Summary\\n\\n"
            f"- run_id: {RUN_ID}\\n"
            f"- install_strategy: {INSTALL_STRATEGY}\\n"
            f"- final_target: {final_target['download_path']}\\n"
            f"- download_mode: {final_target['download_mode']}\\n",
            encoding="utf-8",
        )
        if "google.colab" in sys.modules:
            from google.colab import files  # type: ignore
            files.download(str(final_target["download_path"]))
        print(json.dumps({"final_target": str(final_target["download_path"]), "download_mode": final_target["download_mode"]}, indent=2))
        """
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
    _ = runtime_source, embedded_configs, requirements_text
    _compile_notebook_code_cells(notebook, output_path)
    return notebook


def main() -> None:
    for spec in NOTEBOOK_SPECS:
        output_path = REPO_ROOT / spec["filename"]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        notebook = build_notebook(
            filename=spec["filename"],
            title=spec["title"],
            status=spec["status"],
            run_sanity_only=bool(spec["run_sanity_only"]),
        )
        output_path.write_text(json.dumps(notebook, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"wrote {output_path}")


if __name__ == "__main__":
    main()
