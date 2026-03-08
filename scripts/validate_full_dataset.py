#!/usr/bin/env python3
"""Validate the merged Lumis-1 dataset using the active runtime path."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from lumis1.full_dataset import build_full_dataset_validation_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--full-sft", default="workspace/final/full_sft.jsonl")
    parser.add_argument("--full-preferences", default="workspace/final/full_preferences.jsonl")
    parser.add_argument("--output", default="workspace/reports/full_dataset_validation.json")
    parser.add_argument("--allow-small-sample", action="store_true")
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    report = build_full_dataset_validation_report(
        repo_root,
        full_sft_path=repo_root / args.full_sft,
        full_preferences_path=repo_root / args.full_preferences,
        allow_small_sample=args.allow_small_sample,
    )
    output_path = (repo_root / args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"saved: {output_path}")
    if args.strict and not report["pass"]:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
