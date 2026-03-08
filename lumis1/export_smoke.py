"""GGUF export smoke checks and template parity helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping


class ExportSmokeError(ValueError):
    """Raised when export smoke validation fails."""


def detect_gguf_files(export_dir: str | Path) -> list[str]:
    """List gguf files in export directory."""
    root = Path(export_dir).expanduser().resolve()
    if not root.is_dir():
        raise ExportSmokeError(f"export_dir does not exist: {root}")
    return sorted(p.name for p in root.glob("*.gguf"))


def _contains_variant(files: Iterable[str], token: str) -> bool:
    token_l = token.lower()
    return any(token_l in f.lower() for f in files)


def validate_required_variants(files: Iterable[str]) -> dict[str, bool]:
    """Require at least q8_0 and one q4 variant."""
    listed = list(files)
    return {
        "has_q8_0": _contains_variant(listed, "q8_0"),
        "has_q4_candidate": any(
            marker in f.lower()
            for f in listed
            for marker in ("q4", "q4_k_m", "q4_k_s", "q4_0", "q4_1")
        ),
    }


def is_garbled_text(text: str) -> bool:
    """Detect likely garbled outputs."""
    if not isinstance(text, str) or not text.strip():
        return True
    if "\ufffd" in text:
        return True
    bad = sum(1 for ch in text if ord(ch) < 9 or (13 < ord(ch) < 32))
    return (bad / max(len(text), 1)) > 0.02


def parity_score(reference: str, candidate: str) -> float:
    """Compute lexical overlap score as rough template parity signal."""
    ref_tokens = {t for t in reference.lower().split() if t}
    cand_tokens = {t for t in candidate.lower().split() if t}
    if not ref_tokens and not cand_tokens:
        return 1.0
    if not ref_tokens or not cand_tokens:
        return 0.0
    overlap = len(ref_tokens & cand_tokens)
    union = len(ref_tokens | cand_tokens)
    return overlap / union


def evaluate_template_parity(pairs: Iterable[Mapping[str, Any]], *, min_score: float = 0.25) -> dict[str, Any]:
    """Evaluate parity between HF and GGUF outputs."""
    rows: list[dict[str, Any]] = []
    for idx, pair in enumerate(pairs):
        hf_text = str(pair.get("hf_output", ""))
        gguf_text = str(pair.get("gguf_output", ""))
        score = parity_score(hf_text, gguf_text)
        rows.append(
            {
                "index": idx,
                "prompt": str(pair.get("prompt", "")),
                "score": score,
                "hf_garbled": is_garbled_text(hf_text),
                "gguf_garbled": is_garbled_text(gguf_text),
                "pass": score >= min_score and not is_garbled_text(gguf_text),
            }
        )
    ok = bool(rows) and all(r["pass"] for r in rows)
    return {"ok": ok, "min_score": min_score, "rows": rows}


def run_export_smoke(export_dir: str | Path, parity_pairs: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Run combined GGUF + parity smoke checks."""
    files = detect_gguf_files(export_dir)
    variants = validate_required_variants(files)
    parity = evaluate_template_parity(parity_pairs)
    return {
        "export_dir": str(Path(export_dir).expanduser().resolve()),
        "gguf_files": files,
        "variants": variants,
        "template_parity": parity,
        "ok": variants["has_q8_0"] and variants["has_q4_candidate"] and parity["ok"],
    }
