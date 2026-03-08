"""Dataset filtering and sanitization helpers."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from copy import deepcopy
from typing import Any

from .cot_scrub import (
    CoTMarkerError,
    assert_chat_template_kwargs_thinking_off,
    assert_thinking_off,
    hard_fail_on_cot_markers,
    scrub_cot_text,
)


DEFAULT_PII_FIELDS: tuple[str, ...] = (
    "email",
    "phone",
    "ip",
    "ip_address",
    "user_id",
    "name",
    "first_name",
    "last_name",
    "gender",
    "age",
    "race",
    "ethnicity",
    "religion",
    "sexual_orientation",
    "demographics",
)


def _get_messages(row: Mapping[str, Any]) -> list[dict[str, Any]]:
    messages = row.get("messages")
    if not isinstance(messages, list):
        return []
    return [m for m in messages if isinstance(m, dict)]


def has_empty_user_prompt(row: Mapping[str, Any]) -> bool:
    """Return True if all user text prompts are empty."""
    user_texts: list[str] = []
    for msg in _get_messages(row):
        if msg.get("role") != "user":
            continue
        content = msg.get("content")
        if isinstance(content, str):
            user_texts.append(content.strip())
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    text = part.get("text")
                    if isinstance(text, str):
                        user_texts.append(text.strip())
    return not any(user_texts)


def is_toxic_row(row: Mapping[str, Any]) -> bool:
    """Detect toxic rows via common moderation fields."""
    flags = [
        row.get("toxic"),
        row.get("is_toxic"),
        row.get("toxicity"),
        row.get("flagged_toxicity"),
    ]
    for flag in flags:
        if isinstance(flag, bool) and flag:
            return True
        if isinstance(flag, (int, float)) and flag > 0.7:
            return True
    return False


def strip_pii_fields(row: Mapping[str, Any], pii_fields: Iterable[str] = DEFAULT_PII_FIELDS) -> dict[str, Any]:
    """Return row copy with known PII fields removed from root + metadata."""
    cleaned = deepcopy(dict(row))
    pii_keys = {k.lower() for k in pii_fields}
    for key in list(cleaned.keys()):
        if key.lower() in pii_keys:
            cleaned.pop(key, None)

    metadata = cleaned.get("metadata")
    if isinstance(metadata, dict):
        for key in list(metadata.keys()):
            if key.lower() in pii_keys:
                metadata.pop(key, None)
    return cleaned


def _scrub_message_content(content: Any) -> tuple[Any, int]:
    if isinstance(content, str):
        scrubbed, removed = scrub_cot_text(content)
        return scrubbed, removed
    if isinstance(content, list):
        removed_total = 0
        cleaned_parts: list[Any] = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                text = part.get("text", "")
                if isinstance(text, str):
                    scrubbed, removed = scrub_cot_text(text)
                    new_part = dict(part)
                    new_part["text"] = scrubbed
                    cleaned_parts.append(new_part)
                    removed_total += removed
                    continue
            cleaned_parts.append(part)
        return cleaned_parts, removed_total
    return content, 0


def apply_row_filters(
    rows: Iterable[Mapping[str, Any]],
    *,
    drop_on_cot: bool = True,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Apply required filters and return (kept_rows, report)."""
    row_list = list(rows)
    kept: list[dict[str, Any]] = []
    drop_reasons: Counter[str] = Counter()
    scrubbed_rows = 0

    for row in row_list:
        candidate = strip_pii_fields(row)

        if has_empty_user_prompt(candidate):
            drop_reasons["empty_user_prompt"] += 1
            continue

        if is_toxic_row(candidate):
            drop_reasons["toxic_flagged"] += 1
            continue

        try:
            assert_thinking_off(candidate.get("thinking", "off"))
            assert_chat_template_kwargs_thinking_off(candidate.get("chat_template_kwargs"))
        except Exception:  # noqa: BLE001
            drop_reasons["thinking_not_disabled"] += 1
            continue

        messages = _get_messages(candidate)
        cot_removed = 0
        for msg in messages:
            new_content, removed = _scrub_message_content(msg.get("content"))
            msg["content"] = new_content
            cot_removed += removed

        if cot_removed > 0:
            if drop_on_cot:
                drop_reasons["cot_marker_detected"] += 1
                continue
            scrubbed_rows += 1

        # One more safety pass.
        rejected = False
        for msg in messages:
            content = msg.get("content")
            if isinstance(content, str):
                try:
                    hard_fail_on_cot_markers(content)
                except CoTMarkerError:
                    drop_reasons["cot_marker_remaining"] += 1
                    rejected = True
                    break
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        text = part.get("text")
                        if isinstance(text, str):
                            try:
                                hard_fail_on_cot_markers(text)
                            except CoTMarkerError:
                                drop_reasons["cot_marker_remaining"] += 1
                                rejected = True
                                break
                if rejected:
                    break
        if not rejected:
            kept.append(candidate)

    report = {
        "input_rows": len(row_list),
        "kept_rows": len(kept),
        "dropped_rows": int(sum(drop_reasons.values())),
        "drop_reasons": dict(drop_reasons),
        "scrubbed_rows": scrubbed_rows,
    }
    return kept, report
