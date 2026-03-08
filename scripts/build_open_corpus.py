#!/usr/bin/env python3
"""Deprecated wrapper for the legacy open-corpus script pipeline."""

from __future__ import annotations

import sys


MESSAGE = """build_open_corpus.py is non-canonical and intentionally retired.

Canonical path:
1. notebooks/10_validate_identity_pack.ipynb
2. notebooks/20_build_open_dataset_mix.ipynb
3. notebooks/30_merge_and_validate_full_dataset.ipynb

This wrapper does not execute the old script pipeline because it drifted away from the current config/runtime surface.
"""


def main() -> int:
    print(MESSAGE.rstrip())
    return 2


if __name__ == "__main__":
    sys.exit(main())
