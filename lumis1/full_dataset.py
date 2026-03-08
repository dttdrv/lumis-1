"""Full-dataset validation and manifest helpers for the canonical active path."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .cot_scrub import count_cot_markers
from .hashing import sha256_file
from .identity_pack import iter_jsonl
from .mixing_math import (
    assert_targets,
    composition_from_rows,
    derive_non_identity_multimodal_requirement,
    estimate_row_tokens,
)


CATEGORY_ALIASES: dict[str, str] = {
    "identity": "identity_behavior",
    "general_polished": "polished_general_assistant",
    "real_user": "real_user_conversations",
    "multilingual": "multilingual",
    "utility": "utility_tasks",
}


def load_dataset_mixture_config(repo_root: str | Path) -> dict[str, Any]:
    """Load the active dataset mixture config."""
    root = Path(repo_root).expanduser().resolve()
    payload = yaml.safe_load(
        (root / "configs" / "dataset_mixture.yaml").read_text(encoding="utf-8")
    ) or {}
    if not isinstance(payload, dict):
        raise ValueError("configs/dataset_mixture.yaml must parse to a mapping")
    return payload


def infer_modality(row: dict[str, Any]) -> str:
    """Infer the canonical modality label."""
    modality = row.get("modality")
    if isinstance(modality, str):
        lowered = modality.strip().lower()
        if lowered in {"image_text", "multimodal"}:
            return "image_text"
        if lowered == "text":
            return "text"
    for message in row.get("messages", []):
        if not isinstance(message, dict):
            continue
        content = message.get("content")
        if isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and part.get("type") == "image":
                    return "image_text"
    return "text"


def normalize_category(row: dict[str, Any]) -> str:
    """Normalize current and legacy category labels."""
    category = row.get("category")
    if isinstance(category, str) and category.strip():
        return category.strip()
    bucket = row.get("bucket")
    if isinstance(bucket, str) and bucket.strip():
        return CATEGORY_ALIASES.get(bucket.strip(), bucket.strip())
    return "unknown"


def normalize_source_id(row: dict[str, Any]) -> str:
    """Normalize current and legacy source identifiers."""
    value = row.get("source_id") or row.get("source")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return "unknown"


def normalize_language(row: dict[str, Any]) -> str:
    """Return the best language label available."""
    metadata = row.get("meta")
    if isinstance(metadata, dict):
        value = metadata.get("language")
        if isinstance(value, str) and value.strip():
            return value.strip()
    value = row.get("language")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return "unknown"


def _valid_message(message: dict[str, Any]) -> bool:
    role = message.get("role")
    if role not in {"system", "user", "assistant"}:
        return False
    content = message.get("content")
    if isinstance(content, str):
        return bool(content.strip())
    if isinstance(content, list):
        has_block = False
        for block in content:
            if not isinstance(block, dict):
                continue
            block_type = block.get("type")
            if block_type == "text" and isinstance(block.get("text"), str):
                has_block = True
            elif block_type == "image":
                if any(
                    isinstance(block.get(key), str) and str(block.get(key)).strip()
                    for key in ("image", "image_path", "image_bytes_b64")
                ):
                    has_block = True
        return has_block
    return False


def _validate_sft_row_compat(row: dict[str, Any]) -> tuple[bool, str]:
    if not isinstance(row.get("id"), str) or not row["id"].strip():
        return False, "missing_id"
    messages = row.get("messages")
    if not isinstance(messages, list) or len(messages) < 2:
        return False, "invalid_messages"
    if infer_modality(row) not in {"text", "image_text"}:
        return False, "invalid_modality"
    for message in messages:
        if not isinstance(message, dict) or not _valid_message(message):
            return False, "invalid_message_block"
    return True, "ok"


def _count_cot_markers_in_row(row: dict[str, Any]) -> int:
    total = 0
    for message in row.get("messages", []):
        if not isinstance(message, dict):
            continue
        content = message.get("content")
        if isinstance(content, str):
            total += count_cot_markers(content)
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    text = part.get("text")
                    if isinstance(text, str):
                        total += count_cot_markers(text)
    return total


def normalize_row_for_composition(row: dict[str, Any]) -> dict[str, Any]:
    """Normalize rows for composition math without mutating source data."""
    out = dict(row)
    out["category"] = normalize_category(row)
    out["modality"] = infer_modality(row)
    out["source_id"] = normalize_source_id(row)
    return out


def normalize_preference_row(row: dict[str, Any], idx: int) -> dict[str, Any]:
    """Normalize legacy preference rows for reporting parity."""
    prompt = row.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        prompt_messages = row.get("prompt_messages")
        if isinstance(prompt_messages, list):
            parts: list[str] = []
            for item in prompt_messages:
                if isinstance(item, dict):
                    content = item.get("content")
                    if isinstance(content, str):
                        parts.append(content)
            prompt = " ".join(parts).strip()
    return {
        "id": str(row.get("id") or f"preference-row-{idx:08d}"),
        "source_id": normalize_source_id(row),
        "prompt": str(prompt or "No prompt provided"),
        "chosen": str(row.get("chosen") or ""),
        "rejected": str(row.get("rejected") or ""),
    }


def select_open_sft_rows(
    *,
    identity_rows: list[dict[str, Any]],
    open_rows: list[dict[str, Any]],
    identity_share_target: float,
    allow_small_sample: bool = False,
) -> dict[str, Any]:
    """Select open SFT rows for a canonical or sample-scale full dataset build."""
    identity_tokens = sum(estimate_row_tokens(row) for row in identity_rows)
    if identity_tokens <= 0:
        raise RuntimeError("identity token count must be > 0")
    if identity_share_target <= 0 or identity_share_target >= 1:
        raise RuntimeError(f"invalid identity token share target: {identity_share_target}")

    required_open_tokens_exact = int(
        identity_tokens * ((1.0 - identity_share_target) / identity_share_target)
    )

    if allow_small_sample:
        selected_open = [row for row in open_rows if estimate_row_tokens(row) > 0]
        open_tokens = sum(estimate_row_tokens(row) for row in selected_open)
        return {
            "selected_open_rows": selected_open,
            "identity_tokens": identity_tokens,
            "open_tokens": open_tokens,
            "required_open_tokens_exact": required_open_tokens_exact,
            "remaining_open_tokens": max(required_open_tokens_exact - open_tokens, 0),
            "full_tokens": identity_tokens + open_tokens,
            "identity_token_share_exact": False,
            "selection_mode": "allow_small_sample",
        }

    selected_open: list[dict[str, Any]] = []
    open_tokens = 0
    remaining = required_open_tokens_exact
    for row in open_rows:
        row_tokens = estimate_row_tokens(row)
        if row_tokens <= 0:
            continue
        if row_tokens <= remaining:
            selected_open.append(row)
            remaining -= row_tokens
            open_tokens += row_tokens
        if remaining == 0:
            break

    if remaining != 0:
        raise RuntimeError(
            "could not satisfy exact open token budget. "
            f"target={required_open_tokens_exact}, built={open_tokens}, remaining={remaining}"
        )

    full_tokens = identity_tokens + open_tokens
    if full_tokens != identity_tokens * 5:
        raise RuntimeError(
            "identity token-share exactness failed: "
            f"identity_tokens={identity_tokens}, full_tokens={full_tokens}"
        )

    return {
        "selected_open_rows": selected_open,
        "identity_tokens": identity_tokens,
        "open_tokens": open_tokens,
        "required_open_tokens_exact": required_open_tokens_exact,
        "remaining_open_tokens": 0,
        "full_tokens": full_tokens,
        "identity_token_share_exact": True,
        "selection_mode": "exact_production_shape",
    }


def build_full_dataset_validation_report(
    repo_root: str | Path,
    *,
    full_sft_path: str | Path,
    full_preferences_path: str | Path,
    identity_validation_report: dict[str, Any] | None = None,
    allow_small_sample: bool = False,
) -> dict[str, Any]:
    """Build the canonical full-dataset validation report."""
    root = Path(repo_root).expanduser().resolve()
    mixture = load_dataset_mixture_config(root)
    sft_path = Path(full_sft_path).expanduser().resolve()
    preferences_path = Path(full_preferences_path).expanduser().resolve()
    if not sft_path.exists():
        raise FileNotFoundError(f"Missing full dataset: {sft_path}")
    if not preferences_path.exists():
        raise FileNotFoundError(f"Missing preference dataset: {preferences_path}")

    if identity_validation_report is None:
        identity_report_path = root / "workspace" / "reports" / "identity_validation.json"
        if identity_report_path.exists():
            identity_validation_report = json.loads(
                identity_report_path.read_text(encoding="utf-8")
            )
        else:
            identity_validation_report = {}

    valid_rows: list[dict[str, Any]] = []
    invalid_reasons: dict[str, int] = {}
    category_hist: dict[str, int] = {}
    modality_hist: dict[str, int] = {}
    language_hist: dict[str, int] = {}
    source_hist: dict[str, int] = {}
    cot_marker_count = 0

    for row in iter_jsonl(sft_path):
        ok, reason = _validate_sft_row_compat(row)
        if not ok:
            invalid_reasons[reason] = invalid_reasons.get(reason, 0) + 1
            continue

        normalized = normalize_row_for_composition(row)
        valid_rows.append(normalized)
        cot_marker_count += _count_cot_markers_in_row(row)

        category = normalized["category"]
        modality = normalized["modality"]
        language = normalize_language(row)
        source_id = normalized["source_id"]
        category_hist[category] = category_hist.get(category, 0) + 1
        modality_hist[modality] = modality_hist.get(modality, 0) + 1
        language_hist[language] = language_hist.get(language, 0) + 1
        source_hist[source_id] = source_hist.get(source_id, 0) + 1

    preferences_total = 0
    identity_preference_rows = 0
    preference_prompt_chosen_cot = 0
    for idx, row in enumerate(iter_jsonl(preferences_path), start=1):
        normalized = normalize_preference_row(row, idx)
        preferences_total += 1
        if normalized["source_id"] in {"identity_pack", "identity_pack_preferences"}:
            identity_preference_rows += 1
        for key in ("prompt", "chosen"):
            preference_prompt_chosen_cot += count_cot_markers(normalized[key])

    cot_marker_count += preference_prompt_chosen_cot

    composition = composition_from_rows(
        valid_rows, category_key="category", modality_key="modality"
    )
    category_targets = mixture["targets"]["category_share"]
    modality_targets = mixture["targets"]["modality_share"]
    token_tolerance = float(mixture["targets"]["tolerance"]["token_share_abs"])

    category_tokens = composition["shares"]["category_tokens"]
    modality_tokens = composition["shares"]["modality_tokens"]
    row_category = composition["shares"]["category_rows"]
    row_modality = composition["shares"]["modality_rows"]

    token_category_targets_within_tolerance = True
    token_modality_targets_within_tolerance = True
    if not allow_small_sample:
        try:
            assert_targets(
                category_tokens,
                category_targets,
                tolerance=token_tolerance,
                label="category_tokens",
            )
        except Exception:  # noqa: BLE001
            token_category_targets_within_tolerance = False
        try:
            assert_targets(
                modality_tokens,
                modality_targets,
                tolerance=token_tolerance,
                label="modality_tokens",
            )
        except Exception:  # noqa: BLE001
            token_modality_targets_within_tolerance = False

    total_tokens = int(composition["counts"]["tokens_total"])
    identity_tokens = int(
        composition["counts"]["category_tokens"].get("identity_behavior", 0)
    )
    open_tokens = total_tokens - identity_tokens
    identity_token_share_actual = identity_tokens / max(total_tokens, 1)
    identity_token_share_target = float(
        mixture["identity_pack"]["fixed_share_of_final_sft_tokens"]
    )
    identity_token_share_exact = (
        abs(identity_token_share_actual - identity_token_share_target) <= 1e-12
    )

    identity_mm_share_tokens = float(
        identity_validation_report.get("tokens", {}).get("image_text_share_tokens", 0.0)
    )
    required_non_identity_mm_share_tokens = derive_non_identity_multimodal_requirement(
        overall_multimodal_share=float(modality_targets["image_text"]),
        identity_share=identity_token_share_target,
        identity_multimodal_share=identity_mm_share_tokens,
    )
    non_identity_tokens = total_tokens - identity_tokens
    non_identity_mm_tokens = int(
        sum(
            estimate_row_tokens(row)
            for row in valid_rows
            if row["category"] != "identity_behavior" and row["modality"] == "image_text"
        )
    )
    actual_non_identity_mm_share_tokens = non_identity_mm_tokens / max(non_identity_tokens, 1)
    non_identity_multimodal_share_within_tolerance = (
        abs(actual_non_identity_mm_share_tokens - required_non_identity_mm_share_tokens)
        <= token_tolerance
    )

    row_category_drift = {
        key: abs(float(row_category.get(key, 0.0)) - float(value))
        for key, value in category_targets.items()
    }
    row_modality_drift = {
        key: abs(float(row_modality.get(key, 0.0)) - float(value))
        for key, value in modality_targets.items()
    }

    validations = {
        "cot_marker_count": cot_marker_count,
        "cot_marker_count_zero": cot_marker_count == 0,
        "no_invalid_rows": sum(invalid_reasons.values()) == 0,
        "token_category_targets_within_tolerance": token_category_targets_within_tolerance,
        "token_modality_targets_within_tolerance": token_modality_targets_within_tolerance,
        "identity_token_share_exact": identity_token_share_exact,
        "non_identity_multimodal_share_within_tolerance": non_identity_multimodal_share_within_tolerance,
        "preferences_nonempty": preferences_total > 0,
        "row_drifts_secondary": {
            "category": row_category_drift,
            "modality": row_modality_drift,
        },
    }

    return {
        "input": {
            "full_sft": str(sft_path),
            "full_preferences": str(preferences_path),
            "sha256": {
                "full_sft": sha256_file(sft_path),
                "full_preferences": sha256_file(preferences_path),
            },
        },
        "counts": {
            "sft_rows_total": len(valid_rows),
            "preferences_rows_total": preferences_total,
            "identity_sft_rows": category_hist.get("identity_behavior", 0),
            "identity_preference_rows": identity_preference_rows,
            "invalid_sft_rows": int(sum(invalid_reasons.values())),
            "sft_tokens_total": total_tokens,
            "identity_sft_tokens": identity_tokens,
            "open_sft_tokens": open_tokens,
        },
        "histograms": {
            "category": category_hist,
            "modality": modality_hist,
            "language": language_hist,
            "source": source_hist,
            "invalid_reasons": invalid_reasons,
        },
        "shares": {
            "row_weighted": {
                "category": row_category,
                "modality": row_modality,
            },
            "token_weighted": {
                "category": category_tokens,
                "modality": modality_tokens,
                "identity_token_share": identity_token_share_actual,
            },
            "identity_multimodal_share_tokens": identity_mm_share_tokens,
            "required_non_identity_multimodal_share_tokens": required_non_identity_mm_share_tokens,
            "actual_non_identity_multimodal_share_tokens": actual_non_identity_mm_share_tokens,
        },
        "targets": {
            "category": category_targets,
            "modality": modality_targets,
            "tolerance": mixture["targets"]["tolerance"],
            "identity_token_share": identity_token_share_target,
        },
        "validations": validations,
        "pass": _validation_pass(validations, allow_small_sample=allow_small_sample),
    }


def _validation_pass(validations: dict[str, Any], *, allow_small_sample: bool) -> bool:
    required_keys = [
        "cot_marker_count_zero",
        "no_invalid_rows",
        "non_identity_multimodal_share_within_tolerance",
        "preferences_nonempty",
    ]
    if not allow_small_sample:
        required_keys.extend(
            [
                "token_category_targets_within_tolerance",
                "token_modality_targets_within_tolerance",
                "identity_token_share_exact",
            ]
        )
    return all(bool(validations[key]) for key in required_keys)


def build_dataset_manifest(
    *,
    full_sft_path: str | Path,
    full_preferences_path: str | Path,
    validation_report: dict[str, Any],
    validation_report_path: str | Path,
    created_utc: str | None = None,
) -> dict[str, Any]:
    """Build the canonical dataset manifest."""
    sft_path = Path(full_sft_path).expanduser().resolve()
    preferences_path = Path(full_preferences_path).expanduser().resolve()
    report_path = Path(validation_report_path).expanduser().resolve()
    timestamp = created_utc or datetime.now(timezone.utc).isoformat()
    return {
        "schema_version": "2.0",
        "project": "Lumis-1",
        "created_utc": timestamp,
        "paths": {
            "full_sft": str(sft_path),
            "full_preferences": str(preferences_path),
            "validation_report": str(report_path),
        },
        "sha256": {
            "full_sft": sha256_file(sft_path),
            "full_preferences": sha256_file(preferences_path),
        },
        "counts": validation_report["counts"],
        "shares": validation_report["shares"],
        "targets": validation_report["targets"],
        "validations": validation_report["validations"],
    }


def render_manifest_markdown(manifest: dict[str, Any]) -> str:
    """Render a compact human-readable manifest summary."""
    counts = manifest["counts"]
    shares = manifest["shares"]
    validations = manifest["validations"]
    return "\n".join(
        [
            "# Lumis-1 Dataset Manifest",
            "",
            "Status: Canonical | Descriptive",
            "",
            "This manifest describes the current dataset artifacts only. It does not prove any completed SFT, DPO, evaluation, or export run.",
            "",
            "## Paths",
            f"- Full SFT: `{manifest['paths']['full_sft']}`",
            f"- Full Preferences: `{manifest['paths']['full_preferences']}`",
            f"- Validation Report: `{manifest['paths']['validation_report']}`",
            "",
            "## Counts",
            f"- SFT rows: `{counts['sft_rows_total']}`",
            f"- Preference rows: `{counts['preferences_rows_total']}`",
            f"- Identity SFT rows: `{counts['identity_sft_rows']}`",
            f"- Identity preference rows: `{counts['identity_preference_rows']}`",
            "",
            "## Token Shares",
            f"- Identity token share: `{shares['token_weighted']['identity_token_share']}`",
            f"- Identity multimodal token share: `{shares['identity_multimodal_share_tokens']}`",
            f"- Required non-identity multimodal token share: `{shares['required_non_identity_multimodal_share_tokens']}`",
            f"- Actual non-identity multimodal token share: `{shares['actual_non_identity_multimodal_share_tokens']}`",
            "",
            "## Validation Snapshot",
            f"- CoT marker count: `{validations['cot_marker_count']}`",
            f"- Token category targets within tolerance: `{validations['token_category_targets_within_tolerance']}`",
            f"- Token modality targets within tolerance: `{validations['token_modality_targets_within_tolerance']}`",
            f"- Identity token share exact: `{validations['identity_token_share_exact']}`",
            f"- Non-identity multimodal share within tolerance: `{validations['non_identity_multimodal_share_within_tolerance']}`",
            f"- Preferences non-empty: `{validations['preferences_nonempty']}`",
        ]
    ) + "\n"
