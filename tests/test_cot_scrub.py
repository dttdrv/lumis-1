"""Tests for CoT markers and thinking-off enforcement."""

import pytest

from lumis1.cot_scrub import (
    CoTMarkerError,
    ThinkingModeError,
    assert_chat_template_kwargs_thinking_off,
    assert_thinking_off,
    contains_cot_marker,
    hard_fail_on_cot_markers,
    scrub_cot_text,
)


def test_contains_cot_marker_detects_phrase_variants() -> None:
    assert contains_cot_marker("Chain-of-thought: hidden")
    assert contains_cot_marker("Let's think step by step before answering")


def test_scrub_cot_text_removes_markers() -> None:
    text, removed = scrub_cot_text("<think>hidden</think> final answer")
    assert removed >= 1
    assert "think" not in text.lower()


def test_hard_fail_on_cot_markers_raises() -> None:
    with pytest.raises(CoTMarkerError):
        hard_fail_on_cot_markers("reasoning trace: internal")


def test_assert_thinking_off_accepts_explicit_off_values() -> None:
    for value in (False, "off", "disabled", "false", 0, "0"):
        assert_thinking_off(value)


def test_assert_thinking_off_rejects_non_off_values() -> None:
    with pytest.raises(ThinkingModeError):
        assert_thinking_off(True)


def test_chat_template_kwargs_must_disable_thinking() -> None:
    assert_chat_template_kwargs_thinking_off({"enable_thinking": False})
    with pytest.raises(ThinkingModeError):
        assert_chat_template_kwargs_thinking_off({"enable_thinking": True})
