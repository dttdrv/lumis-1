from __future__ import annotations

import json
from pathlib import Path

from lumis1.run_evidence import (
    assess_eval_export_status,
    create_run_evidence_tree,
    write_run_status,
)


def test_create_run_evidence_tree_and_status_file(tmp_path: Path) -> None:
    paths = create_run_evidence_tree(tmp_path, "eval export 01")
    assert paths["run_root"].name == "eval-export-01"
    assert paths["reports"].is_dir()
    assert paths["checksums"].is_dir()

    status_path = write_run_status(
        tmp_path,
        "eval export 01",
        stage="eval_export",
        status="running",
        details={"hello": "world"},
    )
    payload = json.loads(status_path.read_text(encoding="utf-8"))
    assert payload["run_id"] == "eval-export-01"
    assert payload["stage"] == "eval_export"
    assert payload["status"] == "running"


def test_create_run_evidence_tree_uses_paths_config(tmp_path: Path) -> None:
    configs = tmp_path / "configs"
    configs.mkdir(parents=True, exist_ok=True)
    (configs / "paths.yaml").write_text(
        "\n".join(
            [
                'run_evidence:',
                '  root: "workspace/proof"',
                '  status_file: "STATE.json"',
                '  summary_file: "NOTES.md"',
                '  required_children:',
                '    - "reports"',
                '    - "checksums"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    paths = create_run_evidence_tree(tmp_path, "configured run")
    assert paths["run_root"] == tmp_path / "workspace" / "proof" / "configured-run"
    assert paths["reports"].is_dir()
    assert paths["checksums"].is_dir()
    assert paths["status_file"].name == "STATE.json"
    assert paths["summary_file"].name == "NOTES.md"


def test_assess_eval_export_status_requires_evidence_and_pass_signals(tmp_path: Path) -> None:
    paths = create_run_evidence_tree(tmp_path, "eval export 02")
    for dirname, filename in (
        ("config_snapshot", "inputs.json"),
        ("commands", "command.txt"),
        ("environment", "runtime.json"),
        ("reports", "export_smoke.json"),
        ("checksums", "artifacts.json"),
    ):
        (paths[dirname] / filename).write_text("{}", encoding="utf-8")

    results = {
        "checks": {
            "identity_correctness": {"status": "pass"},
            "multimodal_correctness": {"status": "pass"},
            "vision_hallucination_on_no_image": {"status": "pass"},
        },
        "export_smoke": {"status": "pass"},
    }
    assessment = assess_eval_export_status(
        results=results,
        run_eval=True,
        run_export=True,
        run_paths=paths,
    )
    assert assessment["status"] == "completed"
    assert assessment["blocking_reasons"] == []


def test_assess_eval_export_status_flags_missing_evidence_and_partial_results(
    tmp_path: Path,
) -> None:
    paths = create_run_evidence_tree(tmp_path, "eval export 03")
    assessment = assess_eval_export_status(
        results={
            "checks": {
                "identity_correctness": {"status": "fail"},
                "multimodal_correctness": {"status": "manual_review_required"},
                "vision_hallucination_on_no_image": {"status": "warn"},
            },
            "export_smoke": {"status": "partial"},
        },
        run_eval=True,
        run_export=True,
        run_paths=paths,
    )
    assert assessment["status"] == "needs_review"
    assert "missing_evidence:config_snapshot" in assessment["blocking_reasons"]
    assert "identity_correctness_not_pass" in assessment["blocking_reasons"]
    assert "multimodal_correctness:manual_review_required" in assessment["blocking_reasons"]
    assert "vision_hallucination_on_no_image:warn" in assessment["blocking_reasons"]
    assert "export_smoke:partial" in assessment["blocking_reasons"]
