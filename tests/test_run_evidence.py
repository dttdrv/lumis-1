from __future__ import annotations

import json
from pathlib import Path

from lumis1.run_evidence import assess_eval_export_status, create_run_evidence_tree


def _populate_required_children(run_paths: dict[str, Path]) -> None:
    for child in ("config_snapshot", "commands", "environment", "reports", "checksums"):
        (run_paths[child] / "placeholder.txt").write_text("ok", encoding="utf-8")


def test_assess_eval_export_status_allows_not_applicable_multimodal_and_structural_export(
    tmp_path: Path,
) -> None:
    run_paths = create_run_evidence_tree(tmp_path, "demo-eval")
    _populate_required_children(run_paths)

    results = {
        "checks": {
            "identity_correctness": {"status": "pass"},
            "multimodal_correctness": {"status": "not_applicable"},
            "vision_hallucination_on_no_image": {"status": "pass"},
        },
        "export_smoke": {"status": "structural_only"},
    }

    assessment = assess_eval_export_status(
        results=results,
        run_eval=True,
        run_export=True,
        run_paths=run_paths,
    )

    assert assessment["status"] == "completed"
    assert assessment["blocking_reasons"] == []


def test_assess_eval_export_status_blocks_partial_export_smoke(tmp_path: Path) -> None:
    run_paths = create_run_evidence_tree(tmp_path, "demo-eval")
    _populate_required_children(run_paths)

    results = {
        "checks": {
            "identity_correctness": {"status": "pass"},
            "multimodal_correctness": {"status": "not_applicable"},
            "vision_hallucination_on_no_image": {"status": "pass"},
        },
        "export_smoke": {"status": "partial"},
    }

    assessment = assess_eval_export_status(
        results=results,
        run_eval=True,
        run_export=True,
        run_paths=run_paths,
    )

    assert assessment["status"] == "needs_review"
    assert "export_smoke:partial" in assessment["blocking_reasons"]
