from __future__ import annotations

import json
from pathlib import Path

from lumis1.identity_pack import build_identity_validation_report, resolve_identity_paths


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    _write_text(path, "".join(json.dumps(row) + "\n" for row in rows))


def _make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    _write_text(
        repo / "configs" / "paths.yaml",
        "\n".join(
            [
                'identity_inputs:',
                '  base_dir: "Dataset/identity_dataset/output/full_run_codex_spark_xhigh"',
                '  sft: "Dataset/identity_dataset/output/full_run_codex_spark_xhigh/sft_dataset.jsonl"',
                '  preferences: "Dataset/identity_dataset/output/full_run_codex_spark_xhigh/preference_dataset.jsonl"',
                '  sft_candidates:',
                '    - "Dataset/identity_dataset/output/full_run_codex_spark_xhigh/sft_dataset.jsonl"',
                '    - "Dataset/identity_dataset/output/full_run_codex_spark_xhigh/identity_sft.jsonl"',
                '  preferences_candidates:',
                '    - "Dataset/identity_dataset/output/full_run_codex_spark_xhigh/preference_dataset.jsonl"',
                '    - "Dataset/identity_dataset/output/full_run_codex_spark_xhigh/identity_preferences.jsonl"',
                "",
            ],
        ),
    )
    _write_text(
        repo / "configs" / "dataset_mixture.yaml",
        "\n".join(
            [
                'identity_pack:',
                '  required_counts:',
                '    sft_rows: 1',
                '    preference_rows: 1',
                "",
            ],
        ),
    )
    return repo


def test_resolve_identity_paths_prefers_canonical_artifact_names(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    base = repo / "Dataset" / "identity_dataset" / "output" / "full_run_codex_spark_xhigh"
    _write_jsonl(base / "sft_dataset.jsonl", [{"id": "canonical"}])
    _write_jsonl(base / "identity_sft.jsonl", [{"id": "alias"}])
    _write_jsonl(base / "preference_dataset.jsonl", [{"id": "canonical"}])
    _write_jsonl(base / "identity_preferences.jsonl", [{"id": "alias"}])

    resolved = resolve_identity_paths(repo)
    assert str(resolved["sft"]).endswith("sft_dataset.jsonl")
    assert str(resolved["preferences"]).endswith("preference_dataset.jsonl")


def test_build_identity_validation_report_falls_back_to_alias_paths(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    base = repo / "Dataset" / "identity_dataset" / "output" / "full_run_codex_spark_xhigh"
    _write_jsonl(
        base / "identity_sft.jsonl",
        [
            {
                "id": "row-1",
                "messages": [
                    {"role": "user", "content": [{"type": "text", "text": "Hello"}]},
                    {"role": "assistant", "content": [{"type": "text", "text": "Hi"}]},
                ],
            }
        ],
    )
    _write_jsonl(
        base / "identity_preferences.jsonl",
        [
            {
                "id": "pref-1",
                "prompt": "Hello",
                "chosen": "Hi",
                "rejected": "No",
            }
        ],
    )

    report = build_identity_validation_report(repo, sample_validate_rows=1)
    assert report["counts"]["sft_rows"] == 1
    assert report["counts"]["preference_rows"] == 1
    assert report["identity_paths"]["resolved_sft"].endswith("identity_sft.jsonl")
    assert report["identity_paths"]["resolved_preferences"].endswith(
        "identity_preferences.jsonl"
    )
