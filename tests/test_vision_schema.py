from __future__ import annotations

from pathlib import Path

from PIL import Image

from lumis1.vision_schema import validate_multimodal_row, validate_unsloth_vision_messages


def test_validate_unsloth_vision_messages_accepts_local_image_path(tmp_path: Path) -> None:
    image_path = tmp_path / "sample.png"
    Image.new("RGB", (32, 32), color="white").save(image_path)

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Describe this."},
                {"type": "image", "image_path": str(image_path)},
            ],
        },
        {"role": "assistant", "content": "A white square."},
    ]

    validated = validate_unsloth_vision_messages(messages)
    assert validated[0]["content"][1]["image_path"] == str(image_path)


def test_validate_unsloth_vision_messages_accepts_placeholder_image_uri() -> None:
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Describe this."},
                {"type": "image", "image": "image://seed-0001.jpg"},
            ],
        },
        {"role": "assistant", "content": "Placeholder image prompt."},
    ]

    validated = validate_unsloth_vision_messages(messages)
    assert validated[0]["content"][1]["image"] == "image://seed-0001.jpg"
    assert validated[0]["content"][1]["image_reference_kind"] == "placeholder_uri"


def test_validate_multimodal_row_reports_missing_image() -> None:
    ok, reason = validate_multimodal_row(
        {
            "messages": [
                {"role": "user", "content": [{"type": "text", "text": "Describe this."}]},
                {"role": "assistant", "content": "No image provided."},
            ]
        }
    )
    assert not ok
    assert "user image" in reason.lower()


def test_validate_multimodal_row_accepts_synthetic_placeholder_image() -> None:
    ok, reason = validate_multimodal_row(
        {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe this."},
                        {"type": "image", "image": "synthetic://example/image.png"},
                    ],
                },
                {"role": "assistant", "content": "Placeholder image prompt."},
            ]
        }
    )
    assert ok
    assert reason == "ok"
