#!/usr/bin/env python3
"""Shared utilities for Lumis-1 dataset build scripts."""

from __future__ import annotations

import hashlib
import json
import os
import random
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional

import yaml

try:
    from langdetect import detect as detect_language  # type: ignore
except Exception:  # pragma: no cover
    detect_language = None


def load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def dump_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def count_lines(path: Path) -> int:
    count = 0
    with path.open("r", encoding="utf-8") as f:
        for _ in f:
            count += 1
    return count


def iter_jsonl(path: Path) -> Iterator[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        for idx, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{idx}: {exc}") from exc


def write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1
    return n


def stable_hash_for_record(messages: List[Dict[str, Any]], source: str) -> str:
    payload = json.dumps({"source": source, "messages": messages}, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def normalize_text(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def detect_lang_safe(text: str) -> str:
    text = normalize_text(text)
    if not text:
        return "unknown"
    if detect_language is None:
        return "unknown"
    try:
        return str(detect_language(text))
    except Exception:
        return "unknown"


def is_reasoning_leak(text: str, markers: List[str]) -> bool:
    lower = text.lower()
    return any(m.lower() in lower for m in markers)


def has_fake_tool_claim(text: str, markers: List[str]) -> bool:
    lower = text.lower()
    return any(m.lower() in lower for m in markers)


def build_text_record(
    record_id: str,
    source: str,
    bucket: str,
    user_text: str,
    assistant_text: str,
    language: Optional[str] = None,
    transformed: bool = False,
) -> Dict[str, Any]:
    user_text = normalize_text(user_text)
    assistant_text = normalize_text(assistant_text)
    lang = language or detect_lang_safe(user_text + " " + assistant_text)
    return {
        "id": record_id,
        "source": source,
        "bucket": bucket,
        "modality": "text",
        "messages": [
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": assistant_text},
        ],
        "meta": {"language": lang, "thinking_disabled": True, "transformed": transformed},
    }


def build_multimodal_record(
    record_id: str,
    source: str,
    bucket: str,
    user_text: str,
    image_ref: str,
    assistant_text: str,
    language: Optional[str] = None,
    transformed: bool = False,
) -> Dict[str, Any]:
    user_text = normalize_text(user_text)
    assistant_text = normalize_text(assistant_text)
    lang = language or detect_lang_safe(user_text + " " + assistant_text)
    return {
        "id": record_id,
        "source": source,
        "bucket": bucket,
        "modality": "multimodal",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_text},
                    {"type": "image", "image": image_ref},
                ],
            },
            {"role": "assistant", "content": assistant_text},
        ],
        "meta": {"language": lang, "thinking_disabled": True, "transformed": transformed},
    }


def extract_assistant_text(messages: List[Dict[str, Any]]) -> str:
    for m in reversed(messages):
        if m.get("role") == "assistant":
            content = m.get("content", "")
            if isinstance(content, str):
                return content
            return json.dumps(content, ensure_ascii=False)
    return ""


def canonicalize_messages(raw: Any) -> List[Dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    out: List[Dict[str, Any]] = []
    for m in raw:
        if not isinstance(m, dict):
            continue
        role = str(m.get("role", "")).strip().lower()
        if role not in {"system", "user", "assistant"}:
            continue
        content = m.get("content", "")
        if isinstance(content, list):
            blocks: List[Dict[str, str]] = []
            for b in content:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "text" and isinstance(b.get("text"), str):
                    blocks.append({"type": "text", "text": normalize_text(b["text"])})
                elif b.get("type") == "image" and isinstance(b.get("image"), str):
                    blocks.append({"type": "image", "image": b["image"]})
            if blocks:
                out.append({"role": role, "content": blocks})
        elif isinstance(content, str):
            out.append({"role": role, "content": normalize_text(content)})
    return out


def jaccard_similarity(a: str, b: str) -> float:
    sa = set(normalize_text(a).lower().split())
    sb = set(normalize_text(b).lower().split())
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


@dataclass
class DropCounters:
    values: Counter = field(default_factory=Counter)

    def inc(self, key: str, amount: int = 1) -> None:
        self.values[key] += amount

    def as_dict(self) -> Dict[str, int]:
        return dict(self.values)


def choose_bucket_counts(total: int, bucket_shares: Dict[str, float]) -> Dict[str, int]:
    raw = {k: total * v for k, v in bucket_shares.items()}
    floor = {k: int(v) for k, v in raw.items()}
    remainder = total - sum(floor.values())
    frac_order = sorted(raw.items(), key=lambda kv: kv[1] - int(kv[1]), reverse=True)
    for i in range(remainder):
        floor[frac_order[i % len(frac_order)][0]] += 1
    return floor


def sample_rows(rows: List[Dict[str, Any]], target: int, seed: int = 3407) -> List[Dict[str, Any]]:
    if len(rows) <= target:
        return rows
    rng = random.Random(seed)
    return rng.sample(rows, target)
