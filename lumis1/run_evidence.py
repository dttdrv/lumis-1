"""Run-evidence directory helpers for proof-bearing training and evaluation work."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .identity_pack import load_paths_config

DEFAULT_RUN_CHILDREN: tuple[str, ...] = (
    "config_snapshot",
    "commands",
    "environment",
    "logs",
    "reports",
    "artifacts",
    "checksums",
)

DEFAULT_REQUIRED_NONEMPTY_CHILDREN: tuple[str, ...] = (
    "config_snapshot",
    "commands",
    "environment",
    "reports",
    "checksums",
)


def load_run_evidence_config(repo_root: str | Path) -> dict[str, Any]:
    """Load the configured run-evidence layout with sane defaults."""
    root = Path(repo_root).expanduser().resolve()
    paths_config_path = root / "configs" / "paths.yaml"
    if paths_config_path.exists():
        payload = load_paths_config(root).get("run_evidence", {})
    else:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}
    children = payload.get("required_children")
    if not isinstance(children, list) or not all(
        isinstance(item, str) and item.strip() for item in children
    ):
        children = list(DEFAULT_RUN_CHILDREN)
    return {
        "root": str(payload.get("root") or "workspace/runs"),
        "status_file": str(payload.get("status_file") or "STATUS.json"),
        "summary_file": str(payload.get("summary_file") or "SUMMARY.md"),
        "required_children": tuple(str(item).strip() for item in children),
    }


def sanitize_run_id(run_id: str) -> str:
    """Normalize run ids to safe directory names."""
    if not isinstance(run_id, str) or not run_id.strip():
        raise ValueError("run_id must be a non-empty string")
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", run_id.strip())
    return cleaned.strip("-") or "manual-run"


def create_run_evidence_tree(repo_root: str | Path, run_id: str) -> dict[str, Path]:
    """Create and return the canonical run-evidence directory layout."""
    root = Path(repo_root).expanduser().resolve()
    cfg = load_run_evidence_config(root)
    safe_run_id = sanitize_run_id(run_id)
    run_root = (root / cfg["root"] / safe_run_id).resolve()
    run_root.mkdir(parents=True, exist_ok=True)
    paths = {"run_root": run_root}
    for child in cfg["required_children"]:
        child_path = run_root / child
        child_path.mkdir(parents=True, exist_ok=True)
        paths[child] = child_path
    paths["status_file"] = run_root / cfg["status_file"]
    paths["summary_file"] = run_root / cfg["summary_file"]
    return paths


def write_run_status(
    repo_root: str | Path,
    run_id: str,
    *,
    stage: str,
    status: str,
    details: dict[str, Any] | None = None,
) -> Path:
    """Write the canonical machine-readable run status file."""
    paths = create_run_evidence_tree(repo_root, run_id)
    payload = {
        "run_id": sanitize_run_id(run_id),
        "stage": stage,
        "status": status,
        "updated_utc": datetime.now(timezone.utc).isoformat(),
        "details": details or {},
    }
    paths["status_file"].write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return paths["status_file"]


def write_run_summary(
    repo_root: str | Path,
    run_id: str,
    summary: str,
) -> Path:
    """Write the canonical human-readable run summary file."""
    paths = create_run_evidence_tree(repo_root, run_id)
    paths["summary_file"].write_text(summary.rstrip() + "\n", encoding="utf-8")
    return paths["summary_file"]


def evidence_children_populated(
    paths: dict[str, Path],
    *,
    required_children: tuple[str, ...] = DEFAULT_REQUIRED_NONEMPTY_CHILDREN,
) -> list[str]:
    """Return required evidence children that exist but are still empty."""
    missing: list[str] = []
    for child in required_children:
        child_path = paths[child]
        if not any(child_path.iterdir()):
            missing.append(child)
    return missing


def assess_eval_export_status(
    *,
    results: dict[str, Any],
    run_eval: bool,
    run_export: bool,
    run_paths: dict[str, Path],
) -> dict[str, Any]:
    """Assess whether notebook 60 evidence is strong enough to mark completed."""
    blocking_reasons: list[str] = []

    for child in evidence_children_populated(run_paths):
        blocking_reasons.append(f"missing_evidence:{child}")

    if run_eval:
        identity_status = (
            results.get("checks", {}).get("identity_correctness", {}).get("status")
        )
        if identity_status != "pass":
            blocking_reasons.append("identity_correctness_not_pass")

        mm_status = (
            results.get("checks", {}).get("multimodal_correctness", {}).get("status")
        )
        if mm_status != "pass":
            blocking_reasons.append(f"multimodal_correctness:{mm_status or 'missing'}")

        hallucination_status = (
            results.get("checks", {})
            .get("vision_hallucination_on_no_image", {})
            .get("status")
        )
        if hallucination_status != "pass":
            blocking_reasons.append(
                f"vision_hallucination_on_no_image:{hallucination_status or 'missing'}"
            )

    if run_export:
        export_status = results.get("export_smoke", {}).get("status")
        if export_status != "pass":
            blocking_reasons.append(f"export_smoke:{export_status or 'missing'}")

    return {
        "status": "completed" if not blocking_reasons else "needs_review",
        "blocking_reasons": blocking_reasons,
    }
