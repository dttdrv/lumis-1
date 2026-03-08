"""CoT marker detection and hard thinking-off enforcement utilities."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any


COT_MARKER_PATTERNS: tuple[tuple[str, str], ...] = (
    ("think_open", r"<\s*think\s*>"),
    ("think_close", r"<\s*/\s*think\s*>"),
    ("analysis_open", r"<\s*analysis\s*>"),
    ("analysis_close", r"<\s*/\s*analysis\s*>"),
    ("chain_of_thought", r"chain[- ]of[- ]thought\s*:?\s*"),
    ("lets_think", r"let['’]?s think step by step"),
    ("reasoning_trace", r"reasoning(?:\s+trace|_content)?\s*:?\s*"),
    ("scratchpad", r"scratchpad\s*:?\s*"),
)

_THINKING_OFF_VALUES = {"off", "false", "0", "disabled", "no"}


class CoTMarkerError(ValueError):
    """Raised when disallowed reasoning markers remain in text."""


class ThinkingModeError(ValueError):
    """Raised when thinking is not explicitly disabled."""


def _compiled_patterns() -> list[tuple[str, re.Pattern[str]]]:
    return [(name, re.compile(pattern, re.IGNORECASE)) for name, pattern in COT_MARKER_PATTERNS]


def find_cot_markers(text: str) -> list[str]:
    """Return marker names found in text."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    found: list[str] = []
    for marker_name, pattern in _compiled_patterns():
        if pattern.search(text):
            found.append(marker_name)
    return found


def contains_cot_marker(text: str) -> bool:
    """True when any CoT marker appears."""
    return bool(find_cot_markers(text))


def count_cot_markers(text: str) -> int:
    """Count total marker occurrences in text."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    total = 0
    for _, pattern in _compiled_patterns():
        total += len(pattern.findall(text))
    return total


def scrub_cot_text(text: str) -> tuple[str, int]:
    """Scrub known CoT markers and return (scrubbed_text, markers_removed)."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    scrubbed = text
    removed = 0

    # Remove explicit think/analysis blocks first.
    block_patterns = [
        re.compile(r"<\s*think\s*>.*?<\s*/\s*think\s*>", re.IGNORECASE | re.DOTALL),
        re.compile(r"<\s*analysis\s*>.*?<\s*/\s*analysis\s*>", re.IGNORECASE | re.DOTALL),
    ]
    for pattern in block_patterns:
        matches = len(pattern.findall(scrubbed))
        if matches:
            removed += matches
            scrubbed = pattern.sub(" ", scrubbed)

    # Remove inline markers.
    for _, pattern in _compiled_patterns():
        matches = len(pattern.findall(scrubbed))
        if matches:
            removed += matches
            scrubbed = pattern.sub(" ", scrubbed)

    scrubbed = re.sub(r"\s+", " ", scrubbed).strip()
    return scrubbed, removed


def hard_fail_on_cot_markers(text: str) -> None:
    """Raise when any CoT markers remain."""
    found = find_cot_markers(text)
    if found:
        raise CoTMarkerError(f"disallowed CoT marker(s) found: {', '.join(sorted(found))}")


def assert_no_cot_markers_in_messages(messages: Iterable[Mapping[str, Any]]) -> int:
    """Validate all message content strings and return total marker count."""
    total = 0
    for idx, msg in enumerate(messages):
        content = msg.get("content")
        if isinstance(content, str):
            c = count_cot_markers(content)
            total += c
            if c:
                raise CoTMarkerError(f"messages[{idx}] contains CoT markers")
        elif isinstance(content, list):
            for part_idx, part in enumerate(content):
                if isinstance(part, Mapping) and part.get("type") == "text":
                    text = part.get("text", "")
                    if isinstance(text, str):
                        c = count_cot_markers(text)
                        total += c
                        if c:
                            raise CoTMarkerError(
                                f"messages[{idx}].content[{part_idx}] contains CoT markers"
                            )
    return total


def assert_thinking_off(value: object) -> None:
    """Require thinking to be explicitly disabled."""
    if isinstance(value, bool):
        if not value:
            return
        raise ThinkingModeError("thinking must be explicitly disabled")
    if isinstance(value, int):
        if value == 0:
            return
        raise ThinkingModeError("thinking must be explicitly disabled")
    if isinstance(value, str):
        if value.strip().lower() in _THINKING_OFF_VALUES:
            return
        raise ThinkingModeError("thinking must be explicitly disabled")
    raise ThinkingModeError("thinking must be explicitly disabled")


def assert_chat_template_kwargs_thinking_off(chat_template_kwargs: Mapping[str, Any] | None) -> None:
    """Require chat_template_kwargs.enable_thinking == False when kwargs are present."""
    if chat_template_kwargs is None:
        return
    if not isinstance(chat_template_kwargs, Mapping):
        raise ThinkingModeError("chat_template_kwargs must be a mapping")
    if "enable_thinking" not in chat_template_kwargs:
        raise ThinkingModeError("chat_template_kwargs.enable_thinking is required")
    if chat_template_kwargs.get("enable_thinking") is not False:
        raise ThinkingModeError("chat_template_kwargs.enable_thinking must be false")
