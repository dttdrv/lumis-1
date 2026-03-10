from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from lumis1.colab_unified_unsloth_first import (
    CORE_STACK_PACKAGES,
    IDENTITY_ALLOW_PATTERNS,
    choose_final_download_target,
    create_final_report_payload,
    materialize_processor_ready_sft_rows,
    resolve_dpo_policy,
    resolve_unsloth_matrix_install_command,
    select_supplemental_requirements,
)


def test_select_supplemental_requirements_excludes_core_stack() -> None:
    requirements = [
        "unsloth>=2026.2.0",
        "torch>=2.5.0",
        "transformers>=5.0.0,<6.0.0",
        "datasets>=3.3.0",
        "huggingface-hub>=1.4.0",
        "Pillow>=10.4.0",
        "sentencepiece>=0.2.0",
        "safetensors>=0.6.0",
        "pyyaml>=6.0.2",
    ]

    selected = select_supplemental_requirements(requirements)

    assert "unsloth>=2026.2.0" not in selected
    assert "torch>=2.5.0" not in selected
    assert "transformers>=5.0.0,<6.0.0" not in selected
    assert "datasets>=3.3.0" in selected
    assert "huggingface-hub>=1.4.0" in selected
    assert "Pillow>=10.4.0" in selected
    assert "sentencepiece>=0.2.0" in selected
    assert "safetensors>=0.6.0" in selected
    assert "pyyaml>=6.0.2" in selected
    assert CORE_STACK_PACKAGES >= {
        "unsloth",
        "unsloth_zoo",
        "torch",
        "transformers",
        "trl",
        "accelerate",
        "peft",
        "bitsandbytes",
        "torchvision",
    }


def test_resolve_unsloth_matrix_install_command_for_torch_25_cuda_124() -> None:
    command = resolve_unsloth_matrix_install_command(
        torch_version="2.5.0+cu124",
        cuda_version="12.4",
    )

    assert "unsloth[cu124-torch250]" in command
    assert "git+https://github.com/unslothai/unsloth.git" in command
    assert "unsloth_zoo" in command


def test_identity_allow_patterns_use_canonical_filenames() -> None:
    assert IDENTITY_ALLOW_PATTERNS == [
        "sft_dataset.jsonl",
        "preference_dataset.jsonl",
        "identity_pack_report.pdf",
    ]


def test_materialize_processor_ready_sft_rows_builds_image_objects(tmp_path: Path) -> None:
    image_path = tmp_path / "demo.png"
    Image.new("RGB", (24, 24), (255, 0, 0)).save(image_path)
    rows = [
        {
            "id": "row-1",
            "modality": "image_text",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe the image."},
                        {"type": "image", "image_path": str(image_path)},
                    ],
                },
                {
                    "role": "assistant",
                    "content": [{"type": "text", "text": "A red square."}],
                },
            ],
        }
    ]

    prepared = materialize_processor_ready_sft_rows(rows)

    assert len(prepared) == 1
    assert prepared[0]["id"] == "row-1"
    assert "messages" in prepared[0]
    assert "images" in prepared[0]
    assert len(prepared[0]["images"]) == 1
    assert isinstance(prepared[0]["images"][0], Image.Image)


def test_materialize_processor_ready_sft_rows_rejects_missing_image_path(tmp_path: Path) -> None:
    rows = [
        {
            "id": "row-1",
            "modality": "image_text",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe the image."},
                        {"type": "image", "image_path": str(tmp_path / "missing.png")},
                    ],
                },
                {
                    "role": "assistant",
                    "content": [{"type": "text", "text": "A red square."}],
                },
            ],
        }
    ]

    try:
        materialize_processor_ready_sft_rows(rows)
    except FileNotFoundError as exc:
        assert "missing.png" in str(exc)
    else:
        raise AssertionError("expected FileNotFoundError for missing image_path")


def test_choose_final_download_target_prefers_zip_for_multifile_bundle(tmp_path: Path) -> None:
    gguf = tmp_path / "model-q4_k_m.gguf"
    mmproj = tmp_path / "model.mmproj"
    bundle = tmp_path / "final_deliverables.zip"
    gguf.write_text("demo", encoding="utf-8")
    mmproj.write_text("demo", encoding="utf-8")
    bundle.write_text("demo", encoding="utf-8")

    selected = choose_final_download_target(
        final_export_files=[gguf, mmproj],
        zip_bundle_path=bundle,
        single_file_size_limit_bytes=100_000_000,
    )

    assert selected["download_path"] == bundle
    assert selected["download_mode"] == "zip_bundle"


def test_create_final_report_payload_uses_required_sections() -> None:
    payload = create_final_report_payload(
        what_changed=["Added notebook 91"],
        what_was_verified=["Notebook compile"],
        what_remains_unproven=["Real Colab run"],
        highest_risk_unresolved_issue="Upstream dataset schema drift",
        exact_next_step="Run notebook 91 on Colab G4",
    )

    assert list(payload) == [
        "what_changed",
        "what_was_verified",
        "what_remains_unproven",
        "highest_risk_unresolved_issue",
        "exact_next_step",
    ]
    assert payload["highest_risk_unresolved_issue"] == "Upstream dataset schema drift"


def test_resolve_dpo_policy_skips_text_only_preferences_on_multimodal_run() -> None:
    policy = resolve_dpo_policy(
        is_multimodal_run=True,
        preference_has_images=False,
        experimental_dpo_enabled=False,
    )

    assert policy["status"] == "skipped"
    assert policy["reason"] == "skipped_text_only_preferences_on_multimodal_run"

