from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from lumis1.full_dataset import (
    build_dataset_manifest,
    build_full_dataset_validation_report,
    select_open_sft_rows,
)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    _write_text(path, "".join(json.dumps(row) + "\n" for row in rows))


def _make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    _write_text(
        repo / "configs" / "dataset_mixture.yaml",
        "\n".join(
            [
                'identity_pack:',
                '  required_counts:',
                '    sft_rows: 1',
                '    preference_rows: 1',
                '  fixed_share_of_final_sft_tokens: 0.2',
                'targets:',
                '  category_share:',
                '    polished_general_assistant: 0.3',
                '    real_user_conversations: 0.2',
                '    multilingual: 0.15',
                '    utility_tasks: 0.15',
                '    identity_behavior: 0.2',
                '  modality_share:',
                '    text: 1.0',
                '    image_text: 0.0',
                '  tolerance:',
                '    row_share_abs: 1.0',
                '    token_share_abs: 1.0',
                "",
            ],
        ),
    )
    return repo


def test_full_dataset_validation_report_normalizes_legacy_bucket_and_source_fields(
    tmp_path: Path,
) -> None:
    repo = _make_repo(tmp_path)
    full_sft = repo / "workspace" / "final" / "full_sft.jsonl"
    full_preferences = repo / "workspace" / "final" / "full_preferences.jsonl"
    validation_report_path = repo / "workspace" / "reports" / "full_dataset_validation.json"

    shared_messages = [
        {"role": "user", "content": "hello world"},
        {"role": "assistant", "content": "direct answer"},
    ]
    rows = [
        {"id": "id-1", "source": "identity_pack", "bucket": "identity", "messages": shared_messages},
        {"id": "id-2", "source": "src-a", "bucket": "general_polished", "messages": shared_messages},
        {"id": "id-3", "source": "src-b", "bucket": "general_polished", "messages": shared_messages},
        {"id": "id-4", "source": "src-c", "bucket": "real_user", "messages": shared_messages},
        {"id": "id-5", "source": "src-d", "bucket": "utility", "messages": shared_messages},
    ]
    _write_jsonl(full_sft, rows)
    _write_jsonl(
        full_preferences,
        [
            {
                "id": "pref-1",
                "source": "identity_pack_preferences",
                "prompt_messages": [{"role": "user", "content": "hello"}],
                "chosen": "yes",
                "rejected": "no",
            }
        ],
    )

    report = build_full_dataset_validation_report(
        repo,
        full_sft_path=full_sft,
        full_preferences_path=full_preferences,
        identity_validation_report={"tokens": {"image_text_share_tokens": 0.0}},
        allow_small_sample=True,
    )
    validation_report_path.parent.mkdir(parents=True, exist_ok=True)
    validation_report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    manifest = build_dataset_manifest(
        full_sft_path=full_sft,
        full_preferences_path=full_preferences,
        validation_report=report,
        validation_report_path=validation_report_path,
    )

    assert report["counts"]["identity_sft_rows"] == 1
    assert report["counts"]["identity_preference_rows"] == 1
    assert "identity_behavior" in report["histograms"]["category"]
    assert manifest["paths"]["validation_report"].endswith("full_dataset_validation.json")
    assert manifest["validations"]["preferences_nonempty"] is True


def test_select_open_sft_rows_allows_sample_mode_with_inexact_budget() -> None:
    identity_rows = [
        {
            "id": "id-1",
            "messages": [
                {"role": "user", "content": "hello world"},
                {"role": "assistant", "content": "direct answer"},
            ],
        }
    ]
    open_rows = [
        {
            "id": "open-1",
            "messages": [
                {"role": "user", "content": "tiny"},
                {"role": "assistant", "content": "reply"},
            ],
        }
    ]
    selection = select_open_sft_rows(
        identity_rows=identity_rows,
        open_rows=open_rows,
        identity_share_target=0.2,
        allow_small_sample=True,
    )
    assert selection["selection_mode"] == "allow_small_sample"
    assert len(selection["selected_open_rows"]) == 1
    assert selection["identity_token_share_exact"] is False


def test_render_dataset_manifest_rebuilds_report_for_current_inputs(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    full_sft = repo / "workspace" / "final" / "full_sft.jsonl"
    full_preferences = repo / "workspace" / "final" / "full_preferences.jsonl"
    report_path = repo / "workspace" / "reports" / "full_dataset_validation.json"

    rows = [
        {
            "id": "id-1",
            "source": "identity_pack",
            "bucket": "identity",
            "messages": [
                {"role": "user", "content": "hello world"},
                {"role": "assistant", "content": "direct answer"},
            ],
        }
    ]
    _write_jsonl(full_sft, rows)
    _write_jsonl(
        full_preferences,
        [
            {
                "id": "pref-1",
                "source": "identity_pack_preferences",
                "prompt_messages": [{"role": "user", "content": "hello"}],
                "chosen": "yes",
                "rejected": "no",
            }
        ],
    )
    _write_text(
        report_path,
        json.dumps(
            {
                "input": {
                    "full_sft": "stale",
                    "full_preferences": "stale",
                    "sha256": {"full_sft": "stale", "full_preferences": "stale"},
                },
                "counts": {"sft_rows_total": 999, "preferences_rows_total": 999},
                "shares": {"token_weighted": {"identity_token_share": 0.9}},
                "targets": {"identity_token_share": 0.2},
                "validations": {"preferences_nonempty": True},
                "pass": True,
            },
            indent=2,
        ),
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/render_dataset_manifest.py",
            "--repo-root",
            str(repo),
            "--full-sft",
            "workspace/final/full_sft.jsonl",
            "--full-preferences",
            "workspace/final/full_preferences.jsonl",
            "--validation-report",
            "workspace/reports/full_dataset_validation.json",
            "--output-json",
            "workspace/final/dataset_manifest.json",
            "--output-md",
            "workspace/final/dataset_manifest.md",
            "--allow-small-sample",
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr

    rebuilt_report = json.loads(report_path.read_text(encoding="utf-8"))
    manifest = json.loads(
        (repo / "workspace" / "final" / "dataset_manifest.json").read_text(encoding="utf-8")
    )
    assert rebuilt_report["counts"]["sft_rows_total"] == 1
    assert rebuilt_report["input"]["full_sft"] == str(full_sft.resolve())
    assert manifest["counts"]["sft_rows_total"] == 1
