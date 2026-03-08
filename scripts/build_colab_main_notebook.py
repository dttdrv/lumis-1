from __future__ import annotations

import json
import sys
from pathlib import Path
from textwrap import dedent


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = REPO_ROOT / "notebooks" / "90_colab_main_pipeline.ipynb"


def md(text: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": dedent(text).lstrip("\n").splitlines(keepends=True),
    }


def code(text: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": dedent(text).lstrip("\n").splitlines(keepends=True),
    }


def load_code_cell(relative_path: str, code_index: int) -> str:
    notebook = json.loads((REPO_ROOT / relative_path).read_text(encoding="utf-8"))
    code_cells = [cell for cell in notebook["cells"] if cell.get("cell_type") == "code"]
    return "".join(code_cells[code_index]["source"]).rstrip() + "\n"


def build_open_corpus_cell() -> str:
    source = load_code_cell("notebooks/20_build_open_dataset_mix.ipynb", 0)
    source = source.replace('SOURCE_MODE = "hf"  # \'hf\' or \'local\'', 'SOURCE_MODE = OPEN_SOURCE_MODE  # \'hf\' or \'local\'')
    source = source.replace("DRY_RUN = False", "DRY_RUN = OPEN_DRY_RUN")
    source = source.replace("STREAMING = True", "STREAMING = OPEN_STREAMING")
    return source


def build_merge_cell() -> str:
    source = load_code_cell("notebooks/30_merge_and_validate_full_dataset.ipynb", 0)
    source = source.replace("ALLOW_SMALL_SAMPLE = False", "ALLOW_SMALL_SAMPLE = ALLOW_SMALL_SAMPLE")
    return source


BOOTSTRAP_CELL = """
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


REPO_URL = os.environ.get("LUMIS1_REPO_URL", "https://github.com/dttdrv/lumis-1.git")
REPO_BRANCH = os.environ.get("LUMIS1_REPO_BRANCH") or "main"
COLAB_ROOT = Path("/content")
REPO_ROOT = COLAB_ROOT / "lumis-1"
DRIVE_ROOT = Path("/content/drive/MyDrive/lumis1_store")
IDENTITY_INPUT_DIR = DRIVE_ROOT / "identity" / "full_run_codex_spark_xhigh"
WORKSPACE_PERSIST_ROOT = DRIVE_ROOT / "workspace"
EXPORT_PERSIST_ROOT = DRIVE_ROOT / "exports"

INSTALL_MODE = "repo_pinned"  # "repo_pinned" or "unsloth_auto"
OPEN_SOURCE_MODE = "hf"
OPEN_STREAMING = True
OPEN_DRY_RUN = False
ALLOW_SMALL_SAMPLE = False

PIPELINE_PREFIX = "colab-main-001"
PROFILE = "default_96gb"
FIRST_50_STEPS_SANITY = False

RUN_SFT = True
RUN_DPO = True
RUN_EXPORT = True
RUN_EVAL = True

GGUF_QUANTIZATION_METHODS = ["q8_0", "q4_k_m"]
DOWNLOAD_GGUF_TO_BROWSER = True
DOWNLOAD_GGUF_VARIANT_TOKEN = "q4_k_m"

HF_TOKEN = None


def run(cmd: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True, text=True)


def ensure_repo_checkout() -> None:
    if not REPO_ROOT.exists():
        run(["git", "clone", "-b", REPO_BRANCH, REPO_URL, str(REPO_ROOT)])
    else:
        run(["git", "fetch", "origin"], cwd=REPO_ROOT)
        run(["git", "checkout", REPO_BRANCH], cwd=REPO_ROOT)
        run(["git", "pull", "--ff-only", "origin", REPO_BRANCH], cwd=REPO_ROOT)


def mount_drive_if_available() -> None:
    try:
        from google.colab import drive  # type: ignore
    except Exception:
        return
    if not DRIVE_ROOT.parent.exists():
        drive.mount("/content/drive")


def ensure_symlink(target: Path, link_path: Path) -> None:
    target = target.expanduser().resolve()
    link_path.parent.mkdir(parents=True, exist_ok=True)
    if link_path.is_symlink():
        if link_path.resolve() == target:
            return
        link_path.unlink()
    elif link_path.exists():
        if link_path.is_dir():
            shutil.rmtree(link_path)
        else:
            link_path.unlink()
    os.symlink(str(target), str(link_path), target_is_directory=target.is_dir())


mount_drive_if_available()
ensure_repo_checkout()

WORKSPACE_PERSIST_ROOT.mkdir(parents=True, exist_ok=True)
EXPORT_PERSIST_ROOT.mkdir(parents=True, exist_ok=True)

ensure_symlink(WORKSPACE_PERSIST_ROOT, REPO_ROOT / "workspace")
ensure_symlink(
    IDENTITY_INPUT_DIR,
    REPO_ROOT / "Dataset" / "identity_dataset" / "output" / "full_run_codex_spark_xhigh",
)

from lumis1.identity_pack import DEFAULT_PREFERENCE_NAMES, DEFAULT_SFT_NAMES
from lumis1.main_pipeline import build_main_colab_run_plan

has_sft_file = any((IDENTITY_INPUT_DIR / name).exists() for name in DEFAULT_SFT_NAMES)
has_preference_file = any(
    (IDENTITY_INPUT_DIR / name).exists() for name in DEFAULT_PREFERENCE_NAMES
)
if not (has_sft_file and has_preference_file):
    raise FileNotFoundError(
        "Upload a valid identity artifact folder into IDENTITY_INPUT_DIR before running the pipeline. "
        f"Accepted SFT names: {DEFAULT_SFT_NAMES}; accepted preference names: {DEFAULT_PREFERENCE_NAMES}"
    )

os.chdir(REPO_ROOT)
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

RUN_PLAN = build_main_colab_run_plan(REPO_ROOT, PIPELINE_PREFIX)
print(
    {
        "repo_root": str(REPO_ROOT),
        "identity_input_dir": str(IDENTITY_INPUT_DIR),
        "workspace_root": str(REPO_ROOT / "workspace"),
        "run_plan": {key: str(value) for key, value in RUN_PLAN.items()},
    }
)
"""

INSTALL_CELL = """
from __future__ import annotations

import importlib
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path.cwd().resolve()
required_modules = [
    "datasets",
    "transformers",
    "trl",
    "accelerate",
    "peft",
    "PIL",
    "yaml",
    "unsloth",
    "unsloth_zoo",
]

missing = []
for module_name in required_modules:
    try:
        importlib.import_module(module_name)
    except Exception:
        missing.append(module_name)

if not missing:
    print({"install_mode": INSTALL_MODE, "missing_modules": [], "action": "none"})
else:
    print({"install_mode": INSTALL_MODE, "missing_modules": missing, "action": "install_then_restart"})
    subprocess.run([sys.executable, "-m", "pip", "install", "-U", "pip"], check=True, text=True)
    if INSTALL_MODE == "repo_pinned":
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "-c",
                str(REPO_ROOT / "constraints.txt"),
                "-r",
                str(REPO_ROOT / "requirements.txt"),
            ],
            check=True,
            text=True,
        )
    elif INSTALL_MODE == "unsloth_auto":
        subprocess.run(
            [
                "bash",
                "-lc",
                "wget -qO- https://raw.githubusercontent.com/unslothai/unsloth/main/unsloth/_auto_install.py | python -",
            ],
            check=True,
            text=True,
        )
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "-c",
                str(REPO_ROOT / "constraints.txt"),
                "-r",
                str(REPO_ROOT / "requirements.txt"),
            ],
            check=True,
            text=True,
        )
    else:
        raise ValueError(f"unsupported INSTALL_MODE: {INSTALL_MODE}")

    print("Dependency installation completed. Colab runtime will restart now.")
    os.kill(os.getpid(), 9)
"""

ENV_AND_IDENTITY_CELL = """
from __future__ import annotations

import importlib
import importlib.metadata
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from lumis1.identity_pack import build_identity_validation_report


REPO_ROOT = Path.cwd().resolve()
REPORTS = REPO_ROOT / "workspace" / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)

env = {
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "python": sys.version,
    "platform": platform.platform(),
    "cwd": str(REPO_ROOT),
    "install_mode": INSTALL_MODE,
}

transformers_version = importlib.metadata.version("transformers")
transformers_major = int(transformers_version.split(".")[0])
env["transformers_version"] = transformers_version
env["transformers_major"] = transformers_major
if transformers_major != 5:
    raise RuntimeError(
        f"transformers major version must be 5 for the active Lumis-1 path. Found: {transformers_version}"
    )

for pkg in ("unsloth", "unsloth_zoo", "datasets", "trl", "accelerate", "peft"):
    importlib.import_module(pkg)
    env[f"{pkg}_import"] = True

try:
    import torch

    env["gpu"] = {
        "cuda_available": bool(torch.cuda.is_available()),
        "device_count": int(torch.cuda.device_count()),
        "devices": [
            {
                "index": i,
                "name": torch.cuda.get_device_name(i),
                "total_memory_gb": round(torch.cuda.get_device_properties(i).total_memory / (1024**3), 2),
            }
            for i in range(torch.cuda.device_count())
        ],
    }
except Exception as exc:
    env["gpu"] = {"cuda_available": False, "probe_error": str(exc)}

if HF_TOKEN:
    from huggingface_hub import login

    login(token=HF_TOKEN)
    env["hf_login"] = "performed"
else:
    env["hf_login"] = "skipped"

(REPORTS / "env_sanity.json").write_text(json.dumps(env, indent=2), encoding="utf-8")
freeze = subprocess.run(
    [sys.executable, "-m", "pip", "freeze"],
    capture_output=True,
    text=True,
    check=True,
)
(REPORTS / "env_freeze.txt").write_text(freeze.stdout, encoding="utf-8")

identity_report = build_identity_validation_report(REPO_ROOT)
(REPORTS / "identity_validation.json").write_text(
    json.dumps(identity_report, indent=2),
    encoding="utf-8",
)

print(json.dumps({"env": env, "identity": identity_report}, indent=2))
"""
def build_notebook() -> dict:
    if not OUTPUT_PATH.exists():
        raise FileNotFoundError(
            f"{OUTPUT_PATH} does not exist. This helper currently normalizes the canonical notebook in place and must not create an empty placeholder."
        )
    return json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(build_notebook(), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
