from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = REPO_ROOT / "notebooks" / "90_colab_main_pipeline.ipynb"


def test_colab_main_notebook_exists_and_compiles() -> None:
    assert NOTEBOOK_PATH.exists()

    notebook = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    joined_source = []
    for idx, cell in enumerate(notebook["cells"]):
        if cell.get("cell_type") != "code":
            continue
        source = "".join(cell.get("source", []))
        joined_source.append(source)
        compile(source, f"{NOTEBOOK_PATH}#cell{idx}", "exec")

    all_source = "\n".join(joined_source)
    assert "IDENTITY_INPUT_DIR" in all_source
    assert "RUN_SFT" in all_source
    assert "RUN_DPO" in all_source
    assert "RUN_EXPORT" in all_source
    assert "GGUF_QUANTIZATION_METHODS" in all_source
    assert "save_pretrained_gguf" in all_source
    assert "DOWNLOAD_GGUF_TO_BROWSER" in all_source
    assert "enable_thinking=False" in all_source
    assert "apply_chat_template" in all_source
    assert "STRICT_REPO_PINNED_SYNC" in all_source
    assert 'os.environ.get("LUMIS1_REPO_BRANCH") or "main"' in all_source
    assert "DEFAULT_SFT_NAMES" in all_source
    assert "DEFAULT_PREFERENCE_NAMES" in all_source
    assert "prompt_messages" in all_source
    assert "normalize_identity_preference_row" in all_source
    assert "codex/truth-parity-rehab" not in all_source
