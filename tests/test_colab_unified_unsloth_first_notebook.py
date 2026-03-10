from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_SPECS = [
    {
        "path": REPO_ROOT / "THE NOTEBOOK-sanity.ipynb",
        "title": "THE NOTEBOOK-sanity",
        "run_sanity_only": True,
    },
    {
        "path": REPO_ROOT / "THE NOTEBOOK-updated.ipynb",
        "title": "THE NOTEBOOK-updated",
        "run_sanity_only": False,
    },
]


def test_notebook_surfaces_exist_and_compile() -> None:
    for spec in NOTEBOOK_SPECS:
        notebook_path = spec["path"]
        assert notebook_path.exists()

        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        joined_source: list[str] = []
        for idx, cell in enumerate(notebook["cells"]):
            if cell.get("cell_type") != "code":
                continue
            source = "".join(cell.get("source", []))
            joined_source.append(source)
            compile(source, f"{notebook_path}#cell{idx}", "exec")

        all_source = "\n".join(joined_source)
        assert 'INSTALL_STRATEGY = "unsloth_first"' in all_source
        assert 'PROFILE = "auto"' in all_source
        assert f'# {spec["title"]}' in "".join("".join(cell.get("source", [])) for cell in notebook["cells"] if cell.get("cell_type") == "markdown")
        assert f'RUN_SANITY_ONLY = {str(spec["run_sanity_only"])}' in all_source
        assert "LUMIS1_SANITY_ONLY" not in all_source
        assert "snapshot_download" in all_source
        assert "mount_drive_safely" in all_source
        assert "drive_mount.json" in all_source
        assert "identity_download.json" in all_source
        assert "install_strategy_and_versions.json" in all_source
        assert "files.download" in all_source
        assert "final_deliverables.zip" in all_source
        assert "resolve_dpo_policy" in all_source
        assert "skipped_text_only_preferences_on_multimodal_run" in all_source
        assert f'OUTPUT_PATH = REPO_ROOT / "{notebook_path.name}"' in all_source
        assert "workspace/runs/<run_id>/" not in all_source
        assert "workspace/runs" in all_source
        assert "AutoProcessor" in all_source
        assert "FastVisionModel" in all_source
        assert "FastVisionModel.get_peft_model" in all_source
        assert "UnslothVisionDataCollator" in all_source
        assert "select_notebook_profile" in all_source
        assert 'max_length=int(PROFILE_CFG["sft"]["max_seq_length"])' in all_source
        assert "SFT_MAX_STEPS" in all_source
        assert "choose_final_download_target" in all_source
        assert "materialize_processor_ready_sft_rows" in all_source
        assert "resolve_sft_model_plan" in all_source
        assert "from pathlib import Path" in all_source
        assert "blocking: no final export artifact exists to package or download" in all_source
        assert "from lumis1." not in all_source
        assert 'INSTALL_MODE = "colab_auto"' not in all_source
        assert "STRICT_REPO_PINNED_SYNC" not in all_source
        assert "hf_hub_download" not in all_source
        assert "MAX_RECORDS_SCANNED_PER_SOURCE" in all_source
        assert "MAX_UNMAPPED_ROWS_PER_SOURCE" in all_source
        assert "subset_allowlist_not_embedded" in all_source
        assert "load_in_4bit=True" not in all_source
