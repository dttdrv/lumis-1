"""License and provenance attestation validators."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


PRIVATE_LOCAL_PREFIX = "PRIVATE_LOCAL"
REQUIRED_PRIVATE_LOCAL_FIELDS: tuple[str, ...] = (
    "provenance_attestation",
    "license",
    "redistribution_allowed",
    "pii_policy",
)


class LicenseAttestationError(ValueError):
    """Raised when required legal/provenance attestations are incomplete."""


def is_private_local_source_id(source_id: str) -> bool:
    """Return True for PRIVATE_LOCAL_XX style source ids."""
    return source_id.strip().upper().startswith(PRIVATE_LOCAL_PREFIX)


def _require_non_empty_string(entry: Mapping[str, Any], field: str) -> None:
    value = entry.get(field)
    if not isinstance(value, str) or not value.strip():
        raise LicenseAttestationError(f"missing required string field: {field}")


def validate_private_local_entry(entry: Mapping[str, Any]) -> None:
    """Validate a PRIVATE_LOCAL allowlist entry when enabled=true."""
    source_id = str(entry.get("source_id", ""))
    if not is_private_local_source_id(source_id):
        return
    if entry.get("enabled") is not True:
        return
    source_mode = str(entry.get("source_mode", "")).strip().lower()
    if source_mode != "local":
        raise LicenseAttestationError(f"{source_id}: source_mode must be 'local' when enabled")

    for field in REQUIRED_PRIVATE_LOCAL_FIELDS:
        if field == "redistribution_allowed":
            if not isinstance(entry.get(field), bool):
                raise LicenseAttestationError(
                    f"{source_id}: missing required bool field: {field}"
                )
        else:
            _require_non_empty_string(entry, field)


def require_private_local_attestation(row: Mapping[str, Any]) -> None:
    """Validate row-level attestation fields for PRIVATE_LOCAL rows."""
    source_id = str(row.get("source_id", ""))
    if not is_private_local_source_id(source_id):
        return

    attestation = row.get("private_local_attestation")
    if not isinstance(attestation, Mapping):
        raise LicenseAttestationError(
            f"{source_id}: private_local_attestation mapping is required"
        )

    for field in REQUIRED_PRIVATE_LOCAL_FIELDS:
        value = attestation.get(field)
        if field == "redistribution_allowed":
            if not isinstance(value, bool):
                raise LicenseAttestationError(
                    f"{source_id}: private_local_attestation.{field} must be bool"
                )
        else:
            if not isinstance(value, str) or not value.strip():
                raise LicenseAttestationError(
                    f"{source_id}: private_local_attestation.{field} is required"
                )


def validate_allowlist_sources(entries: Iterable[Mapping[str, Any]]) -> None:
    """Validate all allowlist sources for private-local contracts."""
    for idx, entry in enumerate(entries):
        try:
            validate_private_local_entry(entry)
        except LicenseAttestationError as exc:
            raise LicenseAttestationError(f"sources[{idx}]: {exc}") from exc
