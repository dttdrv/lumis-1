from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
NOTEBOOK_PATH = REPO_ROOT / "notebooks" / "91_colab_unified_unsloth_first.ipynb"
OLD_NOTEBOOK_PATH = REPO_ROOT / "notebooks" / "91_colab_unified_unsloth_first_old.ipynb"


def test_notebook_91_exists_and_compiles() -> None:
    assert NOTEBOOK_PATH.exists()

    notebook = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    joined_source: list[str] = []
    for idx, cell in enumerate(notebook["cells"]):
        if cell.get("cell_type") != "code":
            continue
        source = "".join(cell.get("source", []))
        joined_source.append(source)
        compile(source, f"{NOTEBOOK_PATH}#cell{idx}", "exec")

    all_source = "\n".join(joined_source)
    assert 'INSTALL_STRATEGY = "unsloth_first"' in all_source
    assert "snapshot_download" in all_source
    assert "mount_drive_safely" in all_source
    assert "drive_mount.json" in all_source
    assert "identity_download.json" in all_source
    assert "install_strategy_and_versions.json" in all_source
    assert "files.download" in all_source
    assert "final_deliverables.zip" in all_source
    assert "resolve_dpo_policy" in all_source
    assert "skipped_text_only_preferences_on_multimodal_run" in all_source
    assert 'OUTPUT_PATH = REPO_ROOT / "notebooks" / "91_colab_unified_unsloth_first.ipynb"' in all_source
    assert "workspace/runs/<run_id>/" not in all_source
    assert "workspace/runs" in all_source
    assert "AutoProcessor" in all_source
    assert "FastVisionModel" in all_source
    assert "UnslothVisionDataCollator" in all_source
    assert "max_length=None" in all_source
    assert "choose_final_download_target" in all_source
    assert "materialize_processor_ready_sft_rows" in all_source
    assert "from pathlib import Path" in all_source
    assert "blocking: no final export artifact exists to package or download" in all_source
    assert "from lumis1." not in all_source
    assert 'INSTALL_MODE = "colab_auto"' not in all_source
    assert "STRICT_REPO_PINNED_SYNC" not in all_source
    assert "hf_hub_download" not in all_source


def test_notebook_91_old_exists() -> None:
    assert OLD_NOTEBOOK_PATH.exists()
