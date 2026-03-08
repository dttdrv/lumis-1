"""Dataset row schema validators for Lumis-1."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .cot_scrub import (
    CoTMarkerError,
    ThinkingModeError,
    assert_chat_template_kwargs_thinking_off,
    assert_no_cot_markers_in_messages,
    assert_thinking_off,
    hard_fail_on_cot_markers,
)
from .license_ledger import LicenseAttestationError, require_private_local_attestation
from .vision_schema import VisionSchemaError, validate_unsloth_vision_messages


SCHEMA_VERSION = "1.0"
ALLOWED_ROLES = {"system", "user", "assistant"}
ALLOWED_MODALITIES = {"text", "image_text"}


class SchemaValidationError(ValueError):
    """Raised when row schema is invalid."""


def _extract_prompt_text_from_messages(messages: Any) -> str:
    if not isinstance(messages, Sequence) or isinstance(messages, (str, bytes)):
        return ""

    parts: list[str] = []
    for idx, message in enumerate(messages):
        if not isinstance(message, Mapping):
            raise SchemaValidationError(f"prompt_messages[{idx}] must be a mapping")
        role = message.get("role")
        if role not in ALLOWED_ROLES:
            raise SchemaValidationError(f"prompt_messages[{idx}].role is invalid: {role}")
        content = message.get("content")
        if isinstance(content, str):
            if role == "user" and content.strip():
                parts.append(content.strip())
            continue
        if not isinstance(content, list):
            raise SchemaValidationError(
                f"prompt_messages[{idx}].content must be string or list"
            )
        for block_idx, block in enumerate(content):
            if not isinstance(block, Mapping):
                raise SchemaValidationError(
                    f"prompt_messages[{idx}].content[{block_idx}] must be a mapping"
                )
            if block.get("type") == "text":
                text = block.get("text")
                if isinstance(text, str) and text.strip() and role == "user":
                    parts.append(text.strip())
    return " ".join(parts).strip()


def _require_non_empty_string(data: Mapping[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SchemaValidationError(f"{key} must be a non-empty string")
    return value


def _validate_messages(messages: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    if not isinstance(messages, Sequence) or isinstance(messages, (str, bytes)):
        raise SchemaValidationError("messages must be a sequence")
    if not messages:
        raise SchemaValidationError("messages must not be empty")

    normalized: list[dict[str, Any]] = []
    user_text_found = False
    for idx, msg in enumerate(messages):
        if not isinstance(msg, Mapping):
            raise SchemaValidationError(f"messages[{idx}] must be a mapping")
        role = _require_non_empty_string(msg, "role")
        if role not in ALLOWED_ROLES:
            raise SchemaValidationError(f"messages[{idx}].role is invalid: {role}")
        content = msg.get("content")
        if isinstance(content, str):
            if role == "user" and content.strip():
                user_text_found = True
            try:
                hard_fail_on_cot_markers(content)
            except CoTMarkerError as exc:
                raise SchemaValidationError(str(exc)) from exc
            normalized.append({"role": role, "content": content})
            continue
        if isinstance(content, list):
            normalized.append({"role": role, "content": content})
            for part in content:
                if isinstance(part, Mapping) and part.get("type") == "text":
                    text = part.get("text", "")
                    if isinstance(text, str) and role == "user" and text.strip():
                        user_text_found = True
            continue
        raise SchemaValidationError(f"messages[{idx}].content must be string or list")

    if not user_text_found:
        raise SchemaValidationError("at least one non-empty user prompt is required")

    try:
        assert_no_cot_markers_in_messages(normalized)
    except CoTMarkerError as exc:
        raise SchemaValidationError(str(exc)) from exc
    return normalized


def validate_sft_row(row: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one SFT row."""
    if not isinstance(row, Mapping):
        raise SchemaValidationError("row must be a mapping")

    schema_version = _require_non_empty_string(row, "schema_version")
    if schema_version != SCHEMA_VERSION:
        raise SchemaValidationError(
            f"unsupported schema_version {schema_version}; expected {SCHEMA_VERSION}"
        )

    _require_non_empty_string(row, "id")
    _require_non_empty_string(row, "source_id")
    _require_non_empty_string(row, "license")

    modality = str(row.get("modality", "text")).strip()
    if modality not in ALLOWED_MODALITIES:
        raise SchemaValidationError(f"modality must be one of {sorted(ALLOWED_MODALITIES)}")

    messages = _validate_messages(row.get("messages"))

    try:
        assert_thinking_off(row.get("thinking", "off"))
        assert_chat_template_kwargs_thinking_off(row.get("chat_template_kwargs"))
        require_private_local_attestation(row)
    except (ThinkingModeError, LicenseAttestationError) as exc:
        raise SchemaValidationError(str(exc)) from exc

    normalized = dict(row)
    normalized["messages"] = messages

    if modality == "image_text":
        try:
            normalized["messages"] = validate_unsloth_vision_messages(
                normalized["messages"],
                base_dir=row.get("base_dir"),
                require_user_image=True,
            )
        except VisionSchemaError as exc:
            raise SchemaValidationError(str(exc)) from exc

    return normalized


def validate_preference_row(row: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one preference pair row."""
    if not isinstance(row, Mapping):
        raise SchemaValidationError("preference row must be a mapping")
    _require_non_empty_string(row, "id")
    _require_non_empty_string(row, "source_id")
    _require_non_empty_string(row, "license")
    prompt_messages = row.get("prompt_messages")
    if prompt_messages is not None and not isinstance(prompt_messages, list):
        raise SchemaValidationError("prompt_messages must be a sequence when provided")

    prompt = row.get("prompt")
    if isinstance(prompt, str) and prompt.strip():
        prompt = prompt.strip()
    elif prompt_messages is not None:
        prompt = _extract_prompt_text_from_messages(prompt_messages)
    else:
        prompt = ""
    if not isinstance(prompt, str) or not prompt.strip():
        raise SchemaValidationError("prompt or prompt_messages must provide a non-empty user prompt")

    chosen = _require_non_empty_string(row, "chosen")
    rejected = _require_non_empty_string(row, "rejected")

    try:
        assert_thinking_off(row.get("thinking", "off"))
        assert_chat_template_kwargs_thinking_off(row.get("chat_template_kwargs"))
        require_private_local_attestation(row)
    except (ThinkingModeError, LicenseAttestationError) as exc:
        raise SchemaValidationError(str(exc)) from exc

    try:
        hard_fail_on_cot_markers(prompt)
        hard_fail_on_cot_markers(chosen)
        hard_fail_on_cot_markers(rejected)
    except CoTMarkerError as exc:
        raise SchemaValidationError(str(exc)) from exc

    normalized = dict(row)
    normalized["prompt"] = prompt
    if prompt_messages is None:
        normalized["prompt_messages"] = [{"role": "user", "content": prompt}]
    return normalized


def validate_row(row: Mapping[str, Any]) -> dict[str, Any]:
    """Backward-compatible alias for SFT row validation."""
    return validate_sft_row(row)


def validate_dataset(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Validate list of SFT rows with index-aware errors."""
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        raise SchemaValidationError("rows must be a sequence")
    out: list[dict[str, Any]] = []
    for idx, row in enumerate(rows):
        try:
            out.append(validate_sft_row(row))
        except SchemaValidationError as exc:
            raise SchemaValidationError(f"rows[{idx}]: {exc}") from exc
    return out
