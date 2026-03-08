from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_build_open_corpus_wrapper_routes_to_notebooks() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/build_open_corpus.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "non-canonical" in result.stdout
    assert "notebooks/20_build_open_dataset_mix.ipynb" in result.stdout


def test_merge_full_warehouse_wrapper_routes_to_notebooks() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/merge_full_warehouse.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "non-canonical" in result.stdout
    assert "notebooks/30_merge_and_validate_full_dataset.ipynb" in result.stdout
