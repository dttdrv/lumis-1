from __future__ import annotations

from pathlib import Path

from PIL import Image

from lumis1.colab_standalone import (
    build_multimodal_row_from_record,
    materialize_identity_placeholder_assets,
    render_prompt_messages_to_text,
)


def test_materialize_identity_placeholder_assets_rewrites_image_refs(tmp_path: Path) -> None:
    rows = [
        {
            "id": "identity-1",
            "modality": "multimodal",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "A screenshot is provided. Who are you?"},
                        {"type": "image", "image": "image://identity-seed-0001.jpg"},
                    ],
                },
                {
                    "role": "assistant",
                    "content": [{"type": "text", "text": "I am Lumis-1."}],
                },
            ],
        }
    ]

    materialized, report = materialize_identity_placeholder_assets(rows, tmp_path / "assets")

    assert report["placeholder_blocks_seen"] == 1
    image_block = materialized[0]["messages"][0]["content"][1]
    image_path = image_block["image_path"]
    assert Path(image_path).exists()
    assert image_block["image"] == image_path
    assert image_block["path"] == image_path
    assert materialized[0]["modality"] == "image_text"


def test_build_multimodal_row_from_textvqa_record_materializes_image(tmp_path: Path) -> None:
    image = Image.new("RGB", (64, 64), (255, 0, 0))
    row = build_multimodal_row_from_record(
        "facebook/textvqa",
        {"question": "What color is the sign?", "answers": ["red", "red", "blue"], "image": image},
        asset_root=tmp_path / "assets",
        row_id="textvqa-1",
    )

    assert row is not None
    assert row["modality"] == "image_text"
    image_block = row["messages"][0]["content"][0]
    assert image_block["image_path"]
    assert image_block["image"] == image_block["image_path"]
    assert image_block["path"] == image_block["image_path"]
    assert Path(image_block["image_path"]).exists()
    assert row["messages"][1]["content"][0]["text"] == "red"


def test_build_multimodal_row_from_docmatix_record_uses_first_qa_pair(tmp_path: Path) -> None:
    image = Image.new("RGB", (48, 48), (0, 255, 0))
    row = build_multimodal_row_from_record(
        "HuggingFaceM4/Docmatix",
        {
            "images": [image],
            "texts": [
                {"user": "Read the title.", "assistant": "Invoice 2025"},
                {"user": "Ignore me", "assistant": "Ignore me too"},
            ],
        },
        asset_root=tmp_path / "assets",
        row_id="docmatix-1",
    )

    assert row is not None
    assert row["id"] == "docmatix-1-0"
    assert row["messages"][0]["content"][0]["type"] == "image"
    assert row["messages"][0]["content"][1]["text"] == "Read the title."
    assert row["messages"][1]["content"][0]["text"] == "Invoice 2025"


def test_render_prompt_messages_to_text_ignores_image_blocks() -> None:
    prompt = render_prompt_messages_to_text(
        [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe the image."},
                    {"type": "image", "image_path": "/tmp/demo.png"},
                    {"type": "text", "text": "Be concise."},
                ],
            }
        ]
    )

    assert prompt == "Describe the image. Be concise."
