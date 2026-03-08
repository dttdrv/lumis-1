"""HF Datasets and local JSONL ingestion helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Iterator


class IngestError(ValueError):
    """Raised when source ingestion fails."""


def load_allowlist(path: str | Path) -> dict[str, dict[str, Any]]:
    """Load allowlist YAML and return source_id -> source entry map."""
    import yaml

    allowlist_path = Path(path).expanduser().resolve()
    if not allowlist_path.is_file():
        raise IngestError(f"allowlist path not found: {allowlist_path}")
    payload = yaml.safe_load(allowlist_path.read_text(encoding="utf-8")) or {}
    sources = payload.get("sources")
    if not isinstance(sources, list):
        raise IngestError("allowlist.sources must be a list")
    mapping: dict[str, dict[str, Any]] = {}
    for source in sources:
        if isinstance(source, dict) and isinstance(source.get("source_id"), str):
            mapping[source["source_id"]] = source
    return mapping


def assert_source_allowed(source_id: str, allowlist: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Fail if source is not allowlisted or disabled."""
    source = allowlist.get(source_id)
    if source is None:
        raise IngestError(f"source not in allowlist: {source_id}")
    if source.get("enabled") is not True:
        raise IngestError(f"source is disabled in allowlist: {source_id}")
    return source


def iter_local_jsonl(path: str | Path, *, limit: int | None = None) -> Iterator[dict[str, Any]]:
    """Yield rows from local JSONL file."""
    file_path = Path(path).expanduser().resolve()
    if not file_path.is_file():
        raise IngestError(f"local JSONL file not found: {file_path}")
    with file_path.open("r", encoding="utf-8") as handle:
        for idx, line in enumerate(handle):
            if limit is not None and idx >= limit:
                break
            stripped = line.strip()
            if not stripped:
                continue
            try:
                row = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise IngestError(f"invalid JSON at line {idx + 1} in {file_path}") from exc
            if isinstance(row, dict):
                yield row


def iter_hf_dataset(
    source_id: str,
    *,
    split: str,
    subset: str | None = None,
    streaming: bool = True,
    limit: int | None = None,
) -> Iterable[dict[str, Any]]:
    """Yield rows from HF Datasets using streaming when requested."""
    try:
        from datasets import load_dataset
    except Exception as exc:  # noqa: BLE001
        raise IngestError("datasets package is required for SOURCE_MODE='hf'") from exc

    kwargs: dict[str, Any] = {"split": split, "streaming": streaming}
    dataset_name = source_id
    dataset_subset = subset
    ds = load_dataset(dataset_name, dataset_subset, **kwargs)

    if limit is None:
        for item in ds:
            if isinstance(item, dict):
                yield item
    else:
        for idx, item in enumerate(ds):
            if idx >= limit:
                break
            if isinstance(item, dict):
                yield item


def load_source_records(
    source_entry: dict[str, Any],
    *,
    source_mode: str,
    allowlist: dict[str, dict[str, Any]],
    limit: int | None,
    streaming: bool,
) -> list[dict[str, Any]]:
    """Load records for one source with allowlist enforcement."""
    return list(
        stream_source_records(
            source_entry,
            source_mode=source_mode,
            allowlist=allowlist,
            limit=limit,
            streaming=streaming,
        )
    )


def stream_source_records(
    source_entry: dict[str, Any],
    *,
    source_mode: str,
    allowlist: dict[str, dict[str, Any]],
    limit: int | None,
    streaming: bool,
) -> Iterable[dict[str, Any]]:
    """Yield records for one source with allowlist enforcement."""
    source_id = str(source_entry.get("source_id", ""))
    if not source_id:
        raise IngestError("source_entry missing source_id")
    assert_source_allowed(source_id, allowlist)

    if source_mode == "local":
        local_path = source_entry.get("local_path")
        if not isinstance(local_path, str) or not local_path.strip():
            raise IngestError(f"local source {source_id} missing local_path")
        return iter_local_jsonl(local_path, limit=limit)

    if source_mode == "hf":
        split = str(source_entry.get("split") or source_entry.get("default_split") or "train")
        subset = source_entry.get("subset")
        return iter_hf_dataset(
            source_id,
            split=split,
            subset=subset if isinstance(subset, str) else None,
            streaming=streaming,
            limit=limit,
        )

    raise IngestError("SOURCE_MODE must be 'hf' or 'local'")
