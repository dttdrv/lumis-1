from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = REPO_ROOT / "notebooks" / "90_colab_main_pipeline.ipynb"


def test_colab_main_notebook_exists_and_compiles() -> None:
    assert NOTEBOOK_PATH.exists()

    notebook = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    joined_source = []
    joined_markdown = []
    for idx, cell in enumerate(notebook["cells"]):
        if cell.get("cell_type") == "markdown":
            joined_markdown.append("".join(cell.get("source", [])))
        if cell.get("cell_type") != "code":
            continue
        source = "".join(cell.get("source", []))
        joined_source.append(source)
        compile(source, f"{NOTEBOOK_PATH}#cell{idx}", "exec")

    all_source = "\n".join(joined_source)
    assert "IDENTITY_INPUT_DIR" in all_source
    assert 'IDENTITY_HF_REPO_ID = os.environ.get("LUMIS1_IDENTITY_HF_REPO", "STnoui/lumis1-identity")' in all_source
    assert "IDENTITY_AUTO_DOWNLOAD = True" in all_source
    assert "RUN_SFT" in all_source
    assert "RUN_DPO" in all_source
    assert "RUN_EXPORT" in all_source
    assert "GGUF_QUANTIZATION_METHODS" in all_source
    assert "save_pretrained_gguf" in all_source
    assert "DOWNLOAD_GGUF_TO_BROWSER" in all_source
    assert "enable_thinking=False" in all_source
    assert "apply_chat_template" in all_source
    assert "STRICT_REPO_PINNED_SYNC" in all_source
    assert "EMBEDDED_REQUIREMENTS_TEXT" in all_source
    assert "EMBEDDED_CONSTRAINTS_TEXT" in all_source
    assert "EMBEDDED_RUNTIME_SOURCE" in all_source
    assert "EMBEDDED_CONFIG_TEXT" in all_source
    assert "materialize_identity_placeholder_assets" in all_source
    assert "build_multimodal_row_from_record" in all_source
    assert "render_prompt_messages_to_text" in all_source
    assert "FastVisionModel" in all_source
    assert "UnslothVisionDataCollator" in all_source
    assert "AutoProcessor" in all_source
    assert "materialized_identity_assets" in all_source
    assert "multimodal_eval_samples" in all_source
    assert "prompt_messages" in all_source
    assert "full_preferences.jsonl" in all_source
    assert "AutoPeftModelForCausalLM" in all_source
    assert "huggingface_hub" in all_source
    assert "hf_hub_download" in all_source
    assert "mount_drive_safely" in all_source
    assert "identity_download.json" in all_source
    assert "ensure_identity_inputs()" in all_source
    assert "huggingface-hub>=1.4.0" in all_source
    assert "sentencepiece>=0.2.0" in all_source
    assert "safetensors>=0.6.0" in all_source
    assert "save_processing_assets" in all_source
    assert "DPO_COMPLETED = False" in all_source
    assert "FINAL_MODEL_DIR = DPO_OUTPUT_DIR if DPO_COMPLETED else SFT_OUTPUT_DIR" in all_source
    assert "direct_errors" in all_source
    assert "loader_fallback_error" in all_source
    assert 'PROFILE = "auto"' in all_source
    assert "structural_only" in all_source
    assert "not_applicable" in all_source
    assert "os.kill(os.getpid(), 9)" not in all_source
    assert "from lumis1." not in all_source

    all_markdown = "\n".join(joined_markdown)
    assert "\\n2." not in all_markdown
