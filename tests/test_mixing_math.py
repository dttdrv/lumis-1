"""Tests for composition and target assertions."""

import pytest

from lumis1.mixing_math import (
    MixingMathError,
    allocate_by_weight,
    assert_targets,
    composition_from_rows,
    derive_non_identity_multimodal_requirement,
    normalize_weights,
)


def test_normalize_weights_sums_to_one_and_sorts_keys() -> None:
    normalized = normalize_weights({"b": 3, "a": 1})
    assert list(normalized.keys()) == ["a", "b"]
    assert normalized["a"] == pytest.approx(0.25)
    assert normalized["b"] == pytest.approx(0.75)


def test_allocate_by_weight_is_deterministic_on_ties() -> None:
    allocation = allocate_by_weight(2, {"c": 1, "b": 1, "a": 1})
    assert allocation == {"a": 1, "b": 1, "c": 0}


def test_derive_non_identity_multimodal_requirement_matches_formula() -> None:
    derived = derive_non_identity_multimodal_requirement(
        overall_multimodal_share=0.12,
        identity_share=0.2,
        identity_multimodal_share=0.095,
    )
    assert derived == pytest.approx((0.12 - (0.2 * 0.095)) / 0.8)


def test_composition_from_rows_exposes_row_and_token_shares() -> None:
    rows = [
        {
            "category": "general",
            "modality": "text",
            "messages": [{"role": "user", "content": "hello world"}],
        },
        {
            "category": "identity",
            "modality": "image_text",
            "messages": [{"role": "user", "content": "hello"}],
        },
    ]
    comp = composition_from_rows(rows)
    assert comp["counts"]["rows_total"] == 2
    assert "category_rows" in comp["shares"]
    assert "category_tokens" in comp["shares"]


def test_assert_targets_raises_on_drift() -> None:
    with pytest.raises(MixingMathError):
        assert_targets({"a": 0.5}, {"a": 0.7}, tolerance=0.1, label="row")
