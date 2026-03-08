"""Mixing math for row/token composition and target assertions."""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from typing import Any


class MixingMathError(ValueError):
    """Raised when composition math constraints fail."""


def normalize_weights(weights: Mapping[str, float]) -> dict[str, float]:
    """Normalize non-negative weights to sum to 1."""
    if not weights:
        raise MixingMathError("weights must not be empty")
    cleaned: dict[str, float] = {}
    for key, value in weights.items():
        if not isinstance(key, str) or not key:
            raise MixingMathError("weight keys must be non-empty strings")
        if not isinstance(value, (int, float)):
            raise MixingMathError("weight values must be numeric")
        if float(value) < 0:
            raise MixingMathError("weights must be non-negative")
        cleaned[key] = float(value)
    total = sum(cleaned.values())
    if total <= 0:
        raise MixingMathError("weight sum must be > 0")
    return {k: cleaned[k] / total for k in sorted(cleaned)}


def allocate_by_weight(total_items: int, weights: Mapping[str, float]) -> dict[str, int]:
    """Allocate integer counts using largest remainder with stable tie-breaks."""
    if not isinstance(total_items, int) or total_items < 0:
        raise MixingMathError("total_items must be a non-negative integer")
    normalized = normalize_weights(weights)
    exact = {k: normalized[k] * total_items for k in normalized}
    base = {k: math.floor(v) for k, v in exact.items()}
    remainder = total_items - sum(base.values())
    ranking = sorted(normalized.keys(), key=lambda k: (-(exact[k] - base[k]), k))
    for key in ranking[:remainder]:
        base[key] += 1
    return base


def estimate_token_count(text: str) -> int:
    """Cheap token estimate using word/punctuation chunks."""
    if not isinstance(text, str):
        return 0
    pieces = re.findall(r"\w+|[^\w\s]", text, flags=re.UNICODE)
    return max(len(pieces), 1) if text.strip() else 0


def estimate_row_tokens(row: Mapping[str, Any]) -> int:
    """Estimate tokens for one canonical row."""
    messages = row.get("messages")
    if not isinstance(messages, list):
        return 0
    total = 0
    for msg in messages:
        if not isinstance(msg, Mapping):
            continue
        content = msg.get("content")
        if isinstance(content, str):
            total += estimate_token_count(content)
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, Mapping) and part.get("type") == "text":
                    text = part.get("text")
                    if isinstance(text, str):
                        total += estimate_token_count(text)
    return total


def _share(counter: Mapping[str, float]) -> dict[str, float]:
    total = float(sum(counter.values()))
    if total <= 0:
        return {k: 0.0 for k in sorted(counter)}
    return {k: float(counter[k]) / total for k in sorted(counter)}


def composition_from_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    category_key: str = "category",
    modality_key: str = "modality",
) -> dict[str, Any]:
    """Compute row-weighted and token-weighted category/modality composition."""
    row_category = Counter()
    row_modality = Counter()
    token_category: defaultdict[str, float] = defaultdict(float)
    token_modality: defaultdict[str, float] = defaultdict(float)

    for row in rows:
        category = str(row.get(category_key, "unknown"))
        modality = str(row.get(modality_key, "text"))
        row_category[category] += 1
        row_modality[modality] += 1

        tok = estimate_row_tokens(row)
        token_category[category] += tok
        token_modality[modality] += tok

    return {
        "counts": {
            "rows_total": int(sum(row_category.values())),
            "tokens_total": int(sum(token_category.values())),
            "category_rows": dict(row_category),
            "category_tokens": {k: int(v) for k, v in token_category.items()},
            "modality_rows": dict(row_modality),
            "modality_tokens": {k: int(v) for k, v in token_modality.items()},
        },
        "shares": {
            "category_rows": _share(row_category),
            "category_tokens": _share(token_category),
            "modality_rows": _share(row_modality),
            "modality_tokens": _share(token_modality),
        },
    }


def assert_targets(
    actual_shares: Mapping[str, float],
    target_shares: Mapping[str, float],
    *,
    tolerance: float,
    label: str,
) -> None:
    """Assert absolute drift for each target stays within tolerance."""
    if tolerance < 0:
        raise MixingMathError("tolerance must be non-negative")
    for key, target in target_shares.items():
        actual = float(actual_shares.get(key, 0.0))
        drift = abs(actual - float(target))
        if drift > tolerance:
            raise MixingMathError(
                f"{label} drift for {key} exceeds tolerance: actual={actual:.6f} "
                f"target={target:.6f} drift={drift:.6f} tol={tolerance:.6f}"
            )


def derive_non_identity_multimodal_requirement(
    *,
    overall_multimodal_share: float,
    identity_share: float,
    identity_multimodal_share: float,
) -> float:
    """Compute required non-identity multimodal share.

    Formula:
    (overall - identity_share * identity_mm) / (1 - identity_share)
    """
    if not 0 <= identity_share < 1:
        raise MixingMathError("identity_share must be in [0,1)")
    if not 0 <= overall_multimodal_share <= 1:
        raise MixingMathError("overall_multimodal_share must be in [0,1]")
    if not 0 <= identity_multimodal_share <= 1:
        raise MixingMathError("identity_multimodal_share must be in [0,1]")
    denom = 1.0 - identity_share
    return (overall_multimodal_share - (identity_share * identity_multimodal_share)) / denom
