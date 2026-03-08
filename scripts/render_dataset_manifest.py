#!/usr/bin/env python3
"""Render the canonical dataset manifest for the active Lumis-1 path."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from lumis1.full_dataset import (
    build_dataset_manifest,
    build_full_dataset_validation_report,
    render_manifest_markdown,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--full-sft", default="workspace/final/full_sft.jsonl")
    parser.add_argument("--full-preferences", default="workspace/final/full_preferences.jsonl")
    parser.add_argument("--validation-report", default="workspace/reports/full_dataset_validation.json")
    parser.add_argument("--output-json", default="workspace/final/dataset_manifest.json")
    parser.add_argument("--output-md", default="workspace/final/dataset_manifest.md")
    parser.add_argument("--allow-small-sample", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    validation_report_path = (repo_root / args.validation_report).resolve()
    validation_report = build_full_dataset_validation_report(
        repo_root,
        full_sft_path=repo_root / args.full_sft,
        full_preferences_path=repo_root / args.full_preferences,
        allow_small_sample=args.allow_small_sample,
    )
    validation_report_path.parent.mkdir(parents=True, exist_ok=True)
    validation_report_path.write_text(
        json.dumps(validation_report, indent=2), encoding="utf-8"
    )

    manifest = build_dataset_manifest(
        full_sft_path=repo_root / args.full_sft,
        full_preferences_path=repo_root / args.full_preferences,
        validation_report=validation_report,
        validation_report_path=validation_report_path,
    )

    output_json = (repo_root / args.output_json).resolve()
    output_md = (repo_root / args.output_md).resolve()
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    output_md.write_text(render_manifest_markdown(manifest), encoding="utf-8")
    print(json.dumps({"output_json": str(output_json), "output_md": str(output_md)}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
