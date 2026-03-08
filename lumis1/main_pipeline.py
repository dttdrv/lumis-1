"""Helpers for the single-notebook Colab orchestration path."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml

from .vision_schema import classify_image_block_reference


def sanitize_run_prefix(run_prefix: str) -> str:
    """Normalize a user-facing run prefix to a stable filesystem-safe id."""
    if not isinstance(run_prefix, str) or not run_prefix.strip():
        raise ValueError("run_prefix must be a non-empty string")
    lowered = run_prefix.strip().lower()
    cleaned = re.sub(r"[^a-z0-9._-]+", "-", lowered)
    return cleaned.strip("-") or "colab-main"


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must parse to a mapping")
    return payload


def _iter_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            row = json.loads(stripped)
            if isinstance(row, dict):
                rows.append(row)
    return rows


def _message_content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()
    if not isinstance(content, list):
        return ""
    text_parts: list[str] = []
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get("type") != "text":
            continue
        text = block.get("text")
        if isinstance(text, str) and text.strip():
            text_parts.append(text.strip())
    if text_parts:
        return "\n".join(text_parts)
    return "Image reference omitted for text-only training."


def normalize_messages_for_text_chat_template(messages: Any) -> list[dict[str, str]]:
    """Collapse block-structured message content into plain text for text-only chat templates."""
    if not isinstance(messages, list):
        raise ValueError("messages must be a list")
    normalized: list[dict[str, str]] = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        normalized.append(
            {
                "role": str(message.get("role") or "user"),
                "content": _message_content_to_text(message.get("content")),
            }
        )
    return normalized


def analyze_sft_training_surface(dataset_path: str | Path) -> dict[str, Any]:
    """Inspect one SFT dataset and decide whether text-only fallback is required."""
    path = Path(dataset_path).expanduser().resolve()
    rows = _iter_jsonl(path)

    multimodal_rows = 0
    placeholder_image_rows = 0
    concrete_image_rows = 0

    for row in rows:
        row_has_image = False
        row_has_placeholder = False
        row_has_concrete = False
        for message in row.get("messages", []):
            if not isinstance(message, dict):
                continue
            content = message.get("content")
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict) or block.get("type") != "image":
                    continue
                row_has_image = True
                reference_kind = classify_image_block_reference(block)
                if reference_kind == "placeholder_uri":
                    row_has_placeholder = True
                elif reference_kind in {"image_path", "image_path_like", "image_bytes_b64"}:
                    row_has_concrete = True
        if row_has_image:
            multimodal_rows += 1
        if row_has_placeholder:
            placeholder_image_rows += 1
        if row_has_concrete:
            concrete_image_rows += 1

    if multimodal_rows == 0:
        training_surface = "text_only_native"
    elif concrete_image_rows == 0 and placeholder_image_rows > 0:
        training_surface = "text_only_placeholder_fallback"
    else:
        training_surface = "unverified_concrete_multimodal"

    return {
        "dataset_path": str(path),
        "row_count": len(rows),
        "multimodal_rows": multimodal_rows,
        "placeholder_image_rows": placeholder_image_rows,
        "concrete_image_rows": concrete_image_rows,
        "training_surface": training_surface,
    }


def materialize_text_only_training_dataset(
    source_dataset_path: str | Path,
    output_dataset_path: str | Path,
) -> dict[str, Any]:
    """Write a text-only SFT training dataset from a placeholder-multimodal source."""
    source_path = Path(source_dataset_path).expanduser().resolve()
    output_path = Path(output_dataset_path).expanduser().resolve()
    analysis = analyze_sft_training_surface(source_path)
    if analysis["training_surface"] == "unverified_concrete_multimodal":
        raise RuntimeError(
            "Concrete multimodal image assets detected. The active Colab path is not yet proof-bearing for FastVisionModel training."
        )

    rows = _iter_jsonl(source_path)
    transformed_multimodal_rows = 0
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            rewritten = dict(row)
            messages = []
            row_was_multimodal = False
            for message in row.get("messages", []):
                if not isinstance(message, dict):
                    continue
                rewritten_message = {"role": message.get("role"), "content": _message_content_to_text(message.get("content"))}
                if isinstance(message.get("content"), list):
                    for block in message["content"]:
                        if isinstance(block, dict) and block.get("type") == "image":
                            row_was_multimodal = True
                            break
                messages.append(rewritten_message)
            rewritten["messages"] = messages
            rewritten["modality"] = "text"
            meta = dict(rewritten.get("meta") or {})
            if row_was_multimodal:
                transformed_multimodal_rows += 1
                meta["multimodal_placeholder_collapsed_for_training"] = True
            meta["training_surface"] = analysis["training_surface"]
            rewritten["meta"] = meta
            handle.write(json.dumps(rewritten, ensure_ascii=False) + "\n")

    return {
        **analysis,
        "output_dataset_path": str(output_path),
        "rows_written": len(rows),
        "transformed_multimodal_rows": transformed_multimodal_rows,
    }


def build_main_colab_run_plan(repo_root: str | Path, run_prefix: str) -> dict[str, Path | str]:
    """Build the canonical run layout for the single Colab notebook."""
    root = Path(repo_root).expanduser().resolve()
    prefix = sanitize_run_prefix(run_prefix)
    runs_root = root / "workspace" / "runs"

    sft_run_id = f"{prefix}-sft"
    dpo_run_id = f"{prefix}-dpo"
    export_run_id = f"{prefix}-export"
    eval_run_id = f"{prefix}-eval"

    sft_root = runs_root / sft_run_id
    dpo_root = runs_root / dpo_run_id
    export_root = runs_root / export_run_id
    eval_root = runs_root / eval_run_id

    return {
        "run_prefix": prefix,
        "runs_root": runs_root,
        "sft_run_id": sft_run_id,
        "dpo_run_id": dpo_run_id,
        "export_run_id": export_run_id,
        "eval_run_id": eval_run_id,
        "sft_run_root": sft_root,
        "dpo_run_root": dpo_root,
        "export_run_root": export_root,
        "eval_run_root": eval_root,
        "sft_output_dir": sft_root / "artifacts" / "sft_model",
        "sft_checkpoint_dir": sft_root / "artifacts" / "sft_model" / "checkpoints",
        "dpo_output_dir": dpo_root / "artifacts" / "dpo_model",
        "gguf_dir": export_root / "artifacts" / "gguf",
    }


def resolve_profile_name(
    repo_root: str | Path,
    requested_profile: str | None,
    *,
    gpu_total_memory_gb: float | None = None,
) -> str:
    """Resolve an operator profile, defaulting to the safer option on smaller GPUs."""
    root = Path(repo_root).expanduser().resolve()
    profile_cfg = _load_yaml_mapping(root / "configs" / "run_profiles.yaml")
    profiles = profile_cfg.get("profiles")
    if not isinstance(profiles, dict) or not profiles:
        raise ValueError("configs/run_profiles.yaml must define at least one profile")

    if requested_profile and requested_profile != "auto":
        if requested_profile not in profiles:
            raise ValueError(f"unknown profile: {requested_profile}")
        return requested_profile

    if gpu_total_memory_gb is not None and gpu_total_memory_gb >= 80 and "default_96gb" in profiles:
        return "default_96gb"
    if "safe_fallback" in profiles:
        return "safe_fallback"
    if "default_96gb" in profiles:
        return "default_96gb"
    return next(iter(profiles))


def detect_model_artifact_layout(model_dir: str | Path) -> str:
    """Detect whether a model directory stores PEFT adapters or a full Transformers model."""
    path = Path(model_dir).expanduser().resolve()
    if (path / "adapter_config.json").exists():
        return "peft_adapter"
    if (path / "config.json").exists():
        return "transformers_model"
    return "unknown"


def resolve_sft_runtime(
    repo_root: str | Path,
    *,
    run_plan: dict[str, Path | str],
    profile_name: str,
    run_training: bool,
    first_50_steps_sanity: bool,
) -> dict[str, Any]:
    """Resolve SFT runtime config with run-plan overrides applied in memory."""
    root = Path(repo_root).expanduser().resolve()
    train_cfg = _load_yaml_mapping(root / "configs" / "train_sft.yaml")
    profile_cfg = _load_yaml_mapping(root / "configs" / "run_profiles.yaml")
    chat_cfg = _load_yaml_mapping(root / "configs" / "chat_template_policy.yaml")

    profile = profile_cfg["profiles"][profile_name]["sft"]
    training = dict(train_cfg["training"], **profile)
    if first_50_steps_sanity:
        training["max_steps"] = int(train_cfg["sanity_run"]["max_steps"])

    return {
        "profile": profile_name,
        "run_id": str(run_plan["sft_run_id"]),
        "model": train_cfg["model"],
        "lora": train_cfg["lora"],
        "training": training,
        "chat_template_policy": chat_cfg,
        "dataset_path": str(root / train_cfg["datasets"]["train_sft_path"]),
        "run_training": run_training,
        "output_dir": str(run_plan["sft_output_dir"]),
        "checkpoint_dir": str(run_plan["sft_checkpoint_dir"]),
    }


def resolve_dpo_runtime(
    repo_root: str | Path,
    *,
    run_plan: dict[str, Path | str],
    profile_name: str,
    run_training: bool,
) -> dict[str, Any]:
    """Resolve DPO runtime config with run-plan overrides applied in memory."""
    root = Path(repo_root).expanduser().resolve()
    cfg = _load_yaml_mapping(root / "configs" / "train_dpo.yaml")
    profile_cfg = _load_yaml_mapping(root / "configs" / "run_profiles.yaml")

    profile = profile_cfg["profiles"][profile_name]["dpo"]
    return {
        "profile": profile_name,
        "run_id": str(run_plan["dpo_run_id"]),
        "model": cfg["model"],
        "lora": cfg["lora"],
        "training": dict(cfg["training"], **profile),
        "dpo": cfg["dpo"],
        "preferences": cfg["preferences"],
        "run_training": run_training,
        "output_dir": str(run_plan["dpo_output_dir"]),
        "sft_checkpoint_or_adapter": str(run_plan["sft_output_dir"]),
    }


def build_gguf_export_plan(
    *,
    model_dir: str | Path,
    export_dir: str | Path,
    quantization_methods: list[str] | None = None,
) -> dict[str, Any]:
    """Build the GGUF export plan for the final Colab export step."""
    model_path = Path(model_dir).expanduser().resolve()
    export_path = Path(export_dir).expanduser().resolve()
    methods = quantization_methods or ["q8_0", "q4_k_m"]
    return {
        "model_dir": model_path,
        "export_dir": export_path,
        "quantization_methods": list(methods),
        "zip_path": export_path.parent / "gguf_bundle.zip",
    }
