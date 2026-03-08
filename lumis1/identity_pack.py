"""Canonical identity-pack path resolution and validation helpers."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterator

import yaml

from .cot_scrub import count_cot_markers
from .mixing_math import estimate_row_tokens
from .schema import validate_preference_row, validate_sft_row


DEFAULT_SFT_NAMES: tuple[str, ...] = ("sft_dataset.jsonl", "identity_sft.jsonl")
DEFAULT_PREFERENCE_NAMES: tuple[str, ...] = (
    "preference_dataset.jsonl",
    "identity_preferences.jsonl",
)
DEFAULT_REPORT_NAMES: tuple[str, ...] = ("identity_pack_report.pdf",)


def load_paths_config(repo_root: str | Path) -> dict[str, Any]:
    """Load the canonical paths config."""
    root = Path(repo_root).expanduser().resolve()
    payload = yaml.safe_load((root / "configs" / "paths.yaml").read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError("configs/paths.yaml must parse to a mapping")
    return payload


def load_mixture_config(repo_root: str | Path) -> dict[str, Any]:
    """Load the canonical dataset mixture config."""
    root = Path(repo_root).expanduser().resolve()
    payload = yaml.safe_load(
        (root / "configs" / "dataset_mixture.yaml").read_text(encoding="utf-8")
    ) or {}
    if not isinstance(payload, dict):
        raise ValueError("configs/dataset_mixture.yaml must parse to a mapping")
    return payload


def _candidate_paths(
    repo_root: Path,
    identity_cfg: dict[str, Any],
    *,
    explicit_key: str,
    candidate_key: str,
    fallback_names: tuple[str, ...],
) -> list[Path]:
    out: list[Path] = []
    explicit = identity_cfg.get(explicit_key)
    if isinstance(explicit, str) and explicit.strip():
        out.append((repo_root / explicit).resolve())

    candidates = identity_cfg.get(candidate_key)
    if isinstance(candidates, list):
        for item in candidates:
            if isinstance(item, str) and item.strip():
                out.append((repo_root / item).resolve())

    base = identity_cfg.get("base_dir")
    if isinstance(base, str) and base.strip():
        base_path = (repo_root / base).resolve()
        for name in fallback_names:
            out.append((base_path / name).resolve())

    deduped: list[Path] = []
    seen: set[str] = set()
    for path in out:
        key = str(path)
        if key not in seen:
            deduped.append(path)
            seen.add(key)
    return deduped


def get_identity_candidate_paths(repo_root: str | Path) -> dict[str, list[Path]]:
    """Return ordered candidate paths for canonical identity artifacts."""
    root = Path(repo_root).expanduser().resolve()
    identity_cfg = load_paths_config(root).get("identity_inputs", {})
    if not isinstance(identity_cfg, dict):
        identity_cfg = {}
    return {
        "sft": _candidate_paths(
            root,
            identity_cfg,
            explicit_key="sft",
            candidate_key="sft_candidates",
            fallback_names=DEFAULT_SFT_NAMES,
        ),
        "preferences": _candidate_paths(
            root,
            identity_cfg,
            explicit_key="preferences",
            candidate_key="preferences_candidates",
            fallback_names=DEFAULT_PREFERENCE_NAMES,
        ),
        "report_pdf_optional": _candidate_paths(
            root,
            identity_cfg,
            explicit_key="report_pdf_optional",
            candidate_key="report_pdf_optional_candidates",
            fallback_names=DEFAULT_REPORT_NAMES,
        ),
    }


def resolve_identity_paths(repo_root: str | Path) -> dict[str, Path | None]:
    """Resolve preferred existing identity artifact paths."""
    candidates = get_identity_candidate_paths(repo_root)

    def _pick(paths: list[Path], label: str) -> Path:
        for path in paths:
            if path.exists():
                return path
        raise FileNotFoundError(
            f"Missing required identity {label} file. Checked:\n"
            + "\n".join(str(path) for path in paths)
        )

    pdf_path = next((path for path in candidates["report_pdf_optional"] if path.exists()), None)
    return {
        "sft": _pick(candidates["sft"], "SFT"),
        "preferences": _pick(candidates["preferences"], "preferences"),
        "report_pdf_optional": pdf_path,
    }


def iter_jsonl(path: str | Path) -> Iterator[dict[str, Any]]:
    """Yield JSONL rows."""
    file_path = Path(path).expanduser().resolve()
    with file_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            yield json.loads(stripped)


def _extract_text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts: list[str] = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                text = part.get("text")
                if isinstance(text, str):
                    text_parts.append(text)
        return " ".join(text_parts).strip()
    return ""


def infer_identity_modality(row: dict[str, Any]) -> str:
    """Infer the canonical modality label for identity rows."""
    modality = row.get("modality")
    if isinstance(modality, str):
        lowered = modality.strip().lower()
        if lowered in {"image_text", "multimodal"}:
            return "image_text"
        if lowered == "text":
            return "text"
    if bool(row.get("multimodal")):
        return "image_text"
    for message in row.get("messages", []):
        if not isinstance(message, dict):
            continue
        content = message.get("content")
        if isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and part.get("type") == "image":
                    return "image_text"
    return "text"


def normalize_identity_sft_row(row: dict[str, Any], idx: int) -> dict[str, Any]:
    """Normalize legacy identity SFT rows to the current validator shape."""
    messages = row.get("messages")
    if not isinstance(messages, list):
        user = row.get("prompt") or row.get("user") or "No prompt provided"
        assistant = (
            row.get("response")
            or row.get("output")
            or row.get("assistant")
            or "No response provided"
        )
        messages = [
            {"role": "user", "content": [{"type": "text", "text": str(user)}]},
            {"role": "assistant", "content": [{"type": "text", "text": str(assistant)}]},
        ]
    return {
        "schema_version": "1.0",
        "id": str(row.get("id") or f"identity-sft-{idx:08d}"),
        "source_id": str(row.get("source_id") or row.get("source") or "identity_pack"),
        "license": str(row.get("license") or "operator_provided"),
        "thinking": "off",
        "chat_template_kwargs": {"enable_thinking": False},
        "modality": infer_identity_modality(row),
        "messages": messages,
    }


def validate_identity_sft_row_compat(row: dict[str, Any]) -> None:
    """Validate identity rows while tolerating canonical placeholder image blocks."""
    if row.get("modality") != "image_text":
        validate_sft_row(row)
        return

    coerced = dict(row)
    coerced["modality"] = "text"
    cleaned_messages = []
    for message in row.get("messages", []):
        if not isinstance(message, dict):
            continue
        content = message.get("content")
        if isinstance(content, list):
            text_blocks = [
                part
                for part in content
                if isinstance(part, dict) and part.get("type") == "text"
            ]
            cleaned_messages.append(
                {"role": message.get("role", "user"), "content": text_blocks}
            )
        else:
            cleaned_messages.append(message)
    coerced["messages"] = cleaned_messages
    validate_sft_row(coerced)


def normalize_identity_preference_row(row: dict[str, Any], idx: int) -> dict[str, Any]:
    """Normalize legacy identity preference rows to the current validator shape."""
    prompt = row.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        messages = row.get("messages")
        if isinstance(messages, dict):
            prompt = _extract_text(messages.get("user"))
        elif isinstance(row.get("prompt_messages"), list):
            prompt = " ".join(
                _extract_text(item.get("content"))
                for item in row["prompt_messages"]
                if isinstance(item, dict)
            ).strip()

    chosen = row.get("chosen")
    if not isinstance(chosen, str) or not chosen.strip():
        messages = row.get("messages")
        if isinstance(messages, dict):
            chosen = _extract_text(messages.get("chosen"))

    rejected = row.get("rejected")
    if not isinstance(rejected, str) or not rejected.strip():
        messages = row.get("messages")
        if isinstance(messages, dict):
            rejected = _extract_text(messages.get("rejected"))

    return {
        "id": str(row.get("id") or f"identity-pref-{idx:08d}"),
        "source_id": str(
            row.get("source_id") or row.get("source") or "identity_pack_preferences"
        ),
        "license": str(row.get("license") or "operator_provided"),
        "thinking": "off",
        "chat_template_kwargs": {"enable_thinking": False},
        "prompt": str(prompt or "No prompt provided"),
        "chosen": str(chosen or "No chosen response provided"),
        "rejected": str(rejected or "No rejected response provided"),
    }


def build_identity_validation_report(
    repo_root: str | Path,
    *,
    sample_validate_rows: int = 2000,
) -> dict[str, Any]:
    """Build the canonical identity validation report."""
    root = Path(repo_root).expanduser().resolve()
    paths = resolve_identity_paths(root)
    candidates = get_identity_candidate_paths(root)
    mixture = load_mixture_config(root)

    required_counts = mixture.get("identity_pack", {}).get("required_counts", {})
    expected_sft = int(required_counts.get("sft_rows", 100000))
    expected_preferences = int(required_counts.get("preference_rows", 25000))

    sft_count = 0
    preference_count = 0
    modality_counter: Counter[str] = Counter()
    modality_tokens: Counter[str] = Counter()
    cot_marker_count = 0
    identity_sft_tokens = 0

    for idx, raw_row in enumerate(iter_jsonl(paths["sft"]), start=1):
        row = normalize_identity_sft_row(raw_row, idx)
        sft_count += 1
        if sft_count <= sample_validate_rows:
            validate_identity_sft_row_compat(row)

        modality = row.get("modality")
        if modality not in {"text", "image_text"}:
            modality = "text"
        modality_counter[str(modality)] += 1

        row_tokens = estimate_row_tokens(row)
        identity_sft_tokens += row_tokens
        modality_tokens[str(modality)] += row_tokens

        for message in row.get("messages", []):
            if not isinstance(message, dict):
                continue
            content = message.get("content")
            if isinstance(content, str):
                cot_marker_count += count_cot_markers(content)
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        text = part.get("text")
                        if isinstance(text, str):
                            cot_marker_count += count_cot_markers(text)

    for idx, raw_row in enumerate(iter_jsonl(paths["preferences"]), start=1):
        row = normalize_identity_preference_row(raw_row, idx)
        preference_count += 1
        if preference_count <= sample_validate_rows:
            validate_preference_row(row)
        for key in ("prompt", "chosen", "rejected"):
            value = row.get(key)
            if isinstance(value, str):
                cot_marker_count += count_cot_markers(value)

    if sft_count != expected_sft:
        raise RuntimeError(
            f"identity_sft row count mismatch: expected {expected_sft}, got {sft_count}"
        )
    if preference_count != expected_preferences:
        raise RuntimeError(
            "identity_preferences row count mismatch: "
            f"expected {expected_preferences}, got {preference_count}"
        )

    image_rows = modality_counter.get("image_text", 0)
    identity_mm_share_rows = image_rows / max(sft_count, 1)
    identity_mm_share_tokens = modality_tokens.get("image_text", 0) / max(identity_sft_tokens, 1)

    return {
        "identity_paths": {
            "preferred_sft_candidates": [str(path) for path in candidates["sft"]],
            "preferred_preferences_candidates": [
                str(path) for path in candidates["preferences"]
            ],
            "resolved_sft": str(paths["sft"]),
            "resolved_preferences": str(paths["preferences"]),
            "report_pdf_optional_exists": bool(paths["report_pdf_optional"]),
        },
        "counts": {
            "sft_rows": sft_count,
            "preference_rows": preference_count,
        },
        "tokens": {
            "sft_tokens_total": identity_sft_tokens,
            "text_tokens": modality_tokens.get("text", 0),
            "image_text_tokens": modality_tokens.get("image_text", 0),
            "image_text_share_tokens": identity_mm_share_tokens,
        },
        "modality": {
            "text_rows": modality_counter.get("text", 0),
            "image_text_rows": image_rows,
            "image_text_share": identity_mm_share_rows,
        },
        "cot_marker_count_detected": cot_marker_count,
    }
