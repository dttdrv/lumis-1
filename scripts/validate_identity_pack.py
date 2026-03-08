#!/usr/bin/env python3
"""Validate the canonical Lumis-1 identity pack using the active runtime path."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from lumis1.identity_pack import build_identity_validation_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output", default="workspace/reports/identity_validation.json")
    parser.add_argument("--sample-validate-rows", type=int, default=2000)
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    output_path = (repo_root / args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    report = build_identity_validation_report(
        repo_root,
        sample_validate_rows=args.sample_validate_rows,
    )
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"saved: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
