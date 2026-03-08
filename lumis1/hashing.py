"""Hashing helpers for final artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def stable_json_dumps(data: Any) -> str:
    """Stable JSON serialization for deterministic hashing."""
    return json.dumps(data, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    """Compute sha256 for UTF-8 text."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_object(data: Any) -> str:
    """Compute sha256 for JSON-serializable object."""
    return sha256_text(stable_json_dumps(data))


def sha256_file(path: str | Path, *, chunk_size: int = 1024 * 1024) -> str:
    """Compute sha256 for a file path."""
    file_path = Path(path).expanduser().resolve()
    if not file_path.is_file():
        raise FileNotFoundError(f"file not found: {file_path}")
    digest = hashlib.sha256()
    with file_path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()
