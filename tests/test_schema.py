"""Tests for row schema and private-local attestation enforcement."""

import pytest

from lumis1.schema import (
    SCHEMA_VERSION,
    SchemaValidationError,
    validate_dataset,
    validate_preference_row,
    validate_row,
)


def _valid_private_local_row() -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "id": "row-1",
        "source_id": "PRIVATE_LOCAL_01",
        "license": "custom-internal",
        "modality": "text",
        "thinking": "off",
        "chat_template_kwargs": {"enable_thinking": False},
        "private_local_attestation": {
            "provenance_attestation": "operator attests lawful source",
            "license": "custom-internal",
            "redistribution_allowed": False,
            "pii_policy": "pii removed prior to training",
        },
        "messages": [
            {"role": "user", "content": "Provide a short summary."},
            {"role": "assistant", "content": "Summary output."},
        ],
    }


def test_validate_row_accepts_valid_private_local_row() -> None:
    validated = validate_row(_valid_private_local_row())
    assert validated["id"] == "row-1"


def test_validate_row_requires_private_local_attestation() -> None:
    row = _valid_private_local_row()
    row.pop("private_local_attestation")
    with pytest.raises(SchemaValidationError):
        validate_row(row)


def test_validate_row_hard_fails_cot_markers() -> None:
    row = _valid_private_local_row()
    row["messages"][1]["content"] = "<think>secret reasoning</think>"
    with pytest.raises(SchemaValidationError):
        validate_row(row)


def test_validate_row_requires_chat_template_thinking_off() -> None:
    row = _valid_private_local_row()
    row["chat_template_kwargs"] = {"enable_thinking": True}
    with pytest.raises(SchemaValidationError):
        validate_row(row)


def test_validate_dataset_reports_row_index_on_failure() -> None:
    good = _valid_private_local_row()
    bad = _valid_private_local_row()
    bad["id"] = "row-2"
    bad["thinking"] = "on"
    with pytest.raises(SchemaValidationError, match=r"rows\[1\]"):
        validate_dataset([good, bad])


def test_validate_preference_row_accepts_prompt_messages() -> None:
    row = {
        "id": "pref-1",
        "source_id": "identity_pack_preferences",
        "license": "operator_provided",
        "thinking": "off",
        "chat_template_kwargs": {"enable_thinking": False},
        "private_local_attestation": {
            "provenance_attestation": "operator attests lawful source",
            "license": "operator_provided",
            "redistribution_allowed": False,
            "pii_policy": "pii removed prior to training",
        },
        "prompt_messages": [{"role": "user", "content": "Hello there"}],
        "chosen": "Hi",
        "rejected": "No",
    }

    validated = validate_preference_row(row)

    assert validated["prompt"] == "Hello there"
    assert validated["prompt_messages"][0]["content"] == "Hello there"
