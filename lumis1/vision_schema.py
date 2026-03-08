"""Unsloth multimodal schema validation with PIL checks."""

from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from PIL import Image, UnidentifiedImageError


ALLOWED_ROLES = {"system", "user", "assistant"}
MIN_IMAGE_SIDE = 16
MAX_IMAGE_SIDE = 8192
PLACEHOLDER_IMAGE_URI_PREFIXES = ("image://", "synthetic://")


class VisionSchemaError(ValueError):
    """Raised when multimodal schema or image validation fails."""


def classify_image_block_reference(block: dict[str, Any]) -> str:
    """Classify the image reference type used by one multimodal content block."""
    if isinstance(block.get("image_bytes_b64"), str) and block["image_bytes_b64"].strip():
        return "image_bytes_b64"
    if isinstance(block.get("image_path"), str) and block["image_path"].strip():
        return "image_path"
    image_value = block.get("image")
    if isinstance(image_value, str) and image_value.strip():
        lowered = image_value.strip().lower()
        if lowered.startswith(PLACEHOLDER_IMAGE_URI_PREFIXES):
            return "placeholder_uri"
        return "image_path_like"
    return "missing"


def _load_image_from_path(path_like: str, base_dir: str | Path | None) -> Image.Image:
    # Windows absolute paths like C:\foo\bar.png parse the drive as a URL scheme.
    if Path(path_like).is_absolute():
        image_path = Path(path_like)
    else:
        parsed = urlparse(path_like)
        if parsed.scheme and parsed.scheme not in {"file"}:
            raise VisionSchemaError("image references must be local paths or file:// URIs")
        image_path = Path(parsed.path if parsed.scheme == "file" else path_like)
    if base_dir is not None and not image_path.is_absolute():
        image_path = Path(base_dir) / image_path
    resolved = image_path.expanduser().resolve()
    if not resolved.is_file():
        raise VisionSchemaError(f"image_path not found: {resolved}")
    try:
        with Image.open(resolved) as check:
            check.verify()
        image = Image.open(resolved)
        image.load()
    except (UnidentifiedImageError, OSError) as exc:
        raise VisionSchemaError(f"cannot decode image_path: {resolved}") from exc
    return image


def _load_image_from_b64(encoded: str) -> Image.Image:
    try:
        raw = base64.b64decode(encoded, validate=True)
    except Exception as exc:  # noqa: BLE001
        raise VisionSchemaError("invalid image_bytes_b64 payload") from exc
    try:
        image = Image.open(BytesIO(raw))
        image.load()
    except (UnidentifiedImageError, OSError) as exc:
        raise VisionSchemaError("cannot decode image_bytes_b64 payload") from exc
    return image


def _validate_image_size(image: Image.Image) -> None:
    width, height = image.size
    if width < MIN_IMAGE_SIDE or height < MIN_IMAGE_SIDE:
        raise VisionSchemaError(
            f"image too small ({width}x{height}); minimum is {MIN_IMAGE_SIDE}"
        )
    if width > MAX_IMAGE_SIDE or height > MAX_IMAGE_SIDE:
        raise VisionSchemaError(
            f"image too large ({width}x{height}); maximum is {MAX_IMAGE_SIDE}"
        )


def validate_unsloth_vision_messages(
    messages: list[dict[str, Any]],
    *,
    base_dir: str | Path | None = None,
    require_user_image: bool = True,
) -> list[dict[str, Any]]:
    """Validate Unsloth vision message format and image readability."""
    if not isinstance(messages, list) or not messages:
        raise VisionSchemaError("messages must be a non-empty list")

    normalized: list[dict[str, Any]] = []
    user_image_count = 0

    for idx, message in enumerate(messages):
        if not isinstance(message, dict):
            raise VisionSchemaError(f"messages[{idx}] must be an object")
        role = message.get("role")
        if role not in ALLOWED_ROLES:
            raise VisionSchemaError(f"messages[{idx}].role invalid: {role}")

        content = message.get("content")
        if role == "user":
            if not isinstance(content, list) or not content:
                raise VisionSchemaError(
                    f"messages[{idx}].content must be list blocks for user role"
                )
        if isinstance(content, str):
            if not content.strip():
                raise VisionSchemaError(f"messages[{idx}].content must be non-empty")
            normalized.append({"role": role, "content": content})
            continue
        if not isinstance(content, list) or not content:
            raise VisionSchemaError(f"messages[{idx}].content must be non-empty list")

        blocks: list[dict[str, Any]] = []
        for block_idx, block in enumerate(content):
            if not isinstance(block, dict):
                raise VisionSchemaError(f"messages[{idx}].content[{block_idx}] must be object")
            block_type = block.get("type")
            if block_type == "text":
                text = block.get("text")
                if not isinstance(text, str) or not text.strip():
                    raise VisionSchemaError(
                        f"messages[{idx}].content[{block_idx}].text must be non-empty"
                    )
                blocks.append({"type": "text", "text": text})
            elif block_type == "image":
                image_obj = None
                normalized_image_block: dict[str, Any] = {"type": "image"}
                reference_kind = classify_image_block_reference(block)
                if reference_kind == "image_path":
                    image_obj = _load_image_from_path(block["image_path"], base_dir)
                    normalized_image_block["image_path"] = str(
                        Path(block["image_path"]).expanduser()
                    )
                elif reference_kind == "image_bytes_b64":
                    image_obj = _load_image_from_b64(block["image_bytes_b64"])
                    normalized_image_block["image_bytes_b64"] = block["image_bytes_b64"]
                elif reference_kind == "placeholder_uri":
                    normalized_image_block["image"] = str(block["image"]).strip()
                    normalized_image_block["image_reference_kind"] = "placeholder_uri"
                elif reference_kind == "image_path_like":
                    image_obj = _load_image_from_path(str(block["image"]), base_dir)
                    normalized_image_block["image"] = str(block["image"]).strip()
                else:
                    raise VisionSchemaError(
                        f"messages[{idx}].content[{block_idx}] image block requires image, image_path, or image_bytes_b64"
                    )
                if image_obj is not None:
                    _validate_image_size(image_obj)
                    normalized_image_block["image_reference_kind"] = (
                        "image_path"
                        if reference_kind in {"image_path", "image_path_like"}
                        else "image_bytes_b64"
                    )
                if role == "user":
                    user_image_count += 1
                blocks.append(normalized_image_block)
            else:
                raise VisionSchemaError(
                    f"messages[{idx}].content[{block_idx}].type must be text or image"
                )

        normalized.append({"role": role, "content": blocks})

    if require_user_image and user_image_count == 0:
        raise VisionSchemaError("at least one user image block is required")

    return normalized


def validate_multimodal_row(row: dict[str, Any], *, base_dir: str | Path | None = None) -> tuple[bool, str]:
    """Validate row multimodal payload and return (ok, reason)."""
    try:
        messages = row.get("messages")
        if not isinstance(messages, list):
            return False, "messages_missing_or_invalid"
        validate_unsloth_vision_messages(messages, base_dir=base_dir, require_user_image=True)
    except VisionSchemaError as exc:
        return False, str(exc)
    return True, "ok"
