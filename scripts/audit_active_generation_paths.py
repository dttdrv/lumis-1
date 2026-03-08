#!/usr/bin/env python3
"""Audit generation/API patterns in active pipeline paths.

This audit intentionally scans active execution surfaces separately from legacy archives:
- Active: notebooks/, configs/, lumis1/, scripts/
- Legacy reference: archive/
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable


ACTIVE_DIRS = ("notebooks", "configs", "lumis1", "scripts")
LEGACY_DIRS = ("archive",)

PATTERNS: dict[str, re.Pattern[str]] = {
    "openai": re.compile(r"openai", flags=re.IGNORECASE),
    "anthropic": re.compile(r"anthropic", flags=re.IGNORECASE),
    "nvidia": re.compile(r"nvidia", flags=re.IGNORECASE),
    "together": re.compile(r"together", flags=re.IGNORECASE),
    "deepseek": re.compile(r"deepseek", flags=re.IGNORECASE),
    "requests.post": re.compile(r"requests\.post", flags=re.IGNORECASE),
    "client.chat.completions": re.compile(r"client\.chat\.completions", flags=re.IGNORECASE),
    "generate(": re.compile(r"generate\(", flags=re.IGNORECASE),
}

VIOLATION_KEYS = {
    "openai",
    "anthropic",
    "together",
    "deepseek",
    "requests.post",
    "client.chat.completions",
}

SCAN_EXTENSIONS = {".py", ".ipynb", ".yaml", ".yml", ".md", ".sh", ".txt", ".toml"}
SELF_EXCLUDED_FILES = {"audit_active_generation_paths.py"}


def _iter_files(root: Path, dirs: Iterable[str]) -> Iterable[Path]:
    for rel in dirs:
        base = (root / rel).resolve()
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            if path.name in SELF_EXCLUDED_FILES:
                continue
            if path.suffix.lower() in SCAN_EXTENSIONS:
                yield path


def _scan_paths(root: Path, dirs: Iterable[str]) -> dict[str, list[dict[str, object]]]:
    hits: dict[str, list[dict[str, object]]] = {k: [] for k in PATTERNS}
    for path in _iter_files(root, dirs):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8", errors="ignore")

        lines = text.splitlines()
        for idx, line in enumerate(lines, start=1):
            for key, pattern in PATTERNS.items():
                if pattern.search(line):
                    hits[key].append(
                        {
                            "path": str(path),
                            "line": idx,
                            "line_text": line.strip()[:240],
                        }
                    )
    return hits


def _summarize(hits: dict[str, list[dict[str, object]]]) -> dict[str, object]:
    file_counts = {}
    line_counts = {}
    for key, entries in hits.items():
        line_counts[key] = len(entries)
        file_counts[key] = len({str(e["path"]) for e in entries})
    violation_count = sum(line_counts[k] for k in VIOLATION_KEYS)
    return {
        "line_counts": line_counts,
        "file_counts": file_counts,
        "violation_line_count": violation_count,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument(
        "--output",
        default="workspace/reports/active_generation_audit.json",
    )
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    out_path = (root / args.output).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    active_hits = _scan_paths(root, ACTIVE_DIRS)
    legacy_hits = _scan_paths(root, LEGACY_DIRS)
    active_summary = _summarize(active_hits)
    legacy_summary = _summarize(legacy_hits)

    active_status = (
        "ACTIVE_PIPELINE_GENERATION_PATHS_FOUND"
        if int(active_summary["violation_line_count"]) > 0
        else "ACTIVE_PIPELINE_NO_GENERATION_PATHS_FOUND"
    )

    payload = {
        "active_status": active_status,
        "active_scan_dirs": list(ACTIVE_DIRS),
        "legacy_scan_dirs": list(LEGACY_DIRS),
        "active_summary": active_summary,
        "legacy_summary": legacy_summary,
        "active_hits": active_hits,
        "legacy_hits": legacy_hits,
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(json.dumps(payload, indent=2))
    print(f"saved: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
