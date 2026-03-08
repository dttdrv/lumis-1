#!/usr/bin/env python3
"""Chunk worker for Codex Spark xhigh run."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

from identity_dataset_builder import IdentityDatasetBuilder, Seed, load_or_prepare_config


FORBIDDEN_TOKENS = [
    "internal thoughts",
    "i think step by step",
    "<think>",
    "let me check the web",
    "i have live access",
    "as your browser",
    "i can see your camera feed",
]

ALLOWED_FAILURE_MODES = {
    "too_long",
    "too_vague",
    "identity_drift",
    "wrong_creator",
    "wrong_name",
    "fake_memory",
    "fake_tool",
    "fake_browsing",
    "overconfident",
    "image_hallucinating",
    "cot_leak",
    "off_brand_tone",
    "multilingual_inconsistent",
}

REQ_SFT_KEYS = {
    "id",
    "run_id",
    "source",
    "category",
    "language",
    "messages",
    "messages_flat",
    "seed_id",
    "seed_type",
    "control_note",
    "multimodal",
}

REQ_PREF_KEYS = {
    "id",
    "run_id",
    "source",
    "category",
    "language",
    "multimodal",
    "seed_id",
    "messages",
    "chosen",
    "rejected",
    "chosen_score",
    "rejected_score",
    "margin",
    "failure_modes",
}


def normalize_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text.strip().lower())
    text = re.sub(
        r"[^a-zA-Z0-9\u0600-\u06ff\u0400-\u04ff\u4e00-\u9fff ]+",
        " ",
        text,
    )
    return text


def signature_prompt_assistant(prompt: str, assistant: str) -> str:
    payload = f"{normalize_text(prompt)}\n{normalize_text(assistant)}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def extract_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        parts = []
        for part in value:
            if isinstance(part, dict):
                txt = part.get("text", "")
                if isinstance(txt, str):
                    parts.append(txt)
        return " ".join(parts).strip()
    return ""


def _json_lines(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not path.exists():
        raise FileNotFoundError(f"missing_file:{path}")
    with path.open("r", encoding="utf-8") as f:
        for i, raw in enumerate(f, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception as exc:  # pragma: no cover
                raise ValueError(f"invalid_json:{path.name}:line={i}:{exc}")
    return rows


def read_jsonl(path: Path) -> Tuple[List[Dict[str, Any]], int, str]:
    rows: List[Dict[str, Any]] = []
    bad = 0
    first_error = ""
    try:
        if not path.exists():
            return rows, 1, f"missing_file:{path.name}"
        with path.open("r", encoding="utf-8") as f:
            for lineno, raw in enumerate(f, start=1):
                line = raw.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except Exception as exc:  # pragma: no cover
                    bad += 1
                    if not first_error:
                        first_error = f"line:{lineno}:{exc}"
    except FileNotFoundError:
        return rows, 1, f"missing_file:{path.name}"
    return rows, bad, first_error


def write_jsonl(path: Path, rows: Sequence[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def build_shard_seeds(cfg: Dict[str, Any], rng: random.Random, seed_count: int, seed_prefix: str) -> List[Seed]:
    categories = list(cfg["composition"].keys())
    weights = [cfg["composition"][c] for c in categories]
    langs = cfg["required_languages"]
    seeds: List[Seed] = []

    # Use a dummy builder instance only for deterministic prompt rendering.
    dummy_builder = IdentityDatasetBuilder(cfg, rng, "tmp-run", Path("."))

    for i in range(seed_count):
        category = rng.choices(categories, weights=weights, k=1)[0]
        idx = rng.randrange(len(langs))
        language = "en" if idx % len(langs) == 0 else langs[idx]
        multimodal = category == "multimodal_identity" and rng.random() < 0.95
        prompt = dummy_builder.render_prompt(category, language, multimodal)
        seeds.append(
            Seed(
                seed_id=f"{seed_prefix}-seed-{i + 1:05d}",
                category=category,
                language=language,
                multimodal=multimodal,
                prompt=prompt,
                seed_type="generated",
                control_note=f"cat={category}|lang={language}|mm={multimodal}",
            )
        )

    return seeds


def _forbidden_hit(text: str) -> str:
    lowered = text.lower()
    for tok in FORBIDDEN_TOKENS:
        if tok and tok in lowered:
            return tok
    return ""


def _identity_hit_fail(text: str) -> bool:
    lowered = text.lower()
    return ("lumis-1" not in lowered) or ("eptesicus" not in lowered)


class ReviewResult:
    def __init__(self, ok: bool, message: str, approved_sft: int = 0, approved_pref: int = 0) -> None:
        self.ok = ok
        self.message = message
        self.approved_sft = approved_sft
        self.approved_pref = approved_pref


def validate_sft_row(
    row: Dict[str, Any],
    run_id: str,
    seen_ids: set,
    seen_sigs: set,
) -> Tuple[bool, str]:
    if not isinstance(row, dict):
        return False, "not_object"
    if not REQ_SFT_KEYS.issubset(row.keys()):
        return False, "missing_required_keys"

    row_id = row.get("id")
    if not isinstance(row_id, str) or not row_id:
        return False, "invalid_id"
    if row_id in seen_ids:
        return False, "duplicate_id"

    if row.get("run_id") != run_id:
        return False, "run_id_mismatch"

    messages = row.get("messages")
    if not isinstance(messages, list) or len(messages) < 2:
        return False, "messages_invalid"

    assistant = messages[1]
    chosen_text = extract_text(assistant.get("content", [])) if isinstance(assistant, dict) else ""
    if not chosen_text:
        return False, "assistant_text_empty"

    if _identity_hit_fail(chosen_text):
        return False, "identity_drift"

    forbidden = _forbidden_hit(chosen_text)
    if forbidden:
        return False, f"forbidden:{forbidden}"

    prompt = extract_text(messages[0].get("content", "")) if isinstance(messages[0], dict) else ""
    if not prompt:
        prompt = row.get("messages_flat", {}).get("user", "")
    sig = signature_prompt_assistant(prompt, chosen_text)
    if sig in seen_sigs:
        return False, "exact_duplicate"

    rubric = row.get("rubric", {}) if isinstance(row.get("rubric"), dict) else {}
    total = rubric.get("total")
    if isinstance(total, (int, float)) and total < 84.0:
        return False, "low_score"

    seen_ids.add(row_id)
    seen_sigs.add(sig)
    return True, ""


def validate_pref_row(
    row: Dict[str, Any],
    run_id: str,
    seen_ids: set,
    seen_sigs: set,
) -> Tuple[bool, str]:
    if not isinstance(row, dict):
        return False, "not_object"
    if not REQ_PREF_KEYS.issubset(row.keys()):
        return False, "missing_required_keys"

    row_id = row.get("id")
    if not isinstance(row_id, str) or not row_id:
        return False, "invalid_id"
    if row_id in seen_ids:
        return False, "duplicate_id"

    if row.get("run_id") != run_id:
        return False, "run_id_mismatch"

    messages = row.get("messages")
    if not isinstance(messages, dict):
        return False, "messages_invalid"
    user_text = extract_text(messages.get("user", []))
    chosen_text = extract_text(messages.get("chosen", []))
    _rejected_text = extract_text(messages.get("rejected", []))
    user_field = row.get("messages_flat", {}).get("user")
    chosen_field = row.get("chosen")
    rejected_field = row.get("rejected")
    if not isinstance(chosen_field, str) or not chosen_field.strip():
        return False, "chosen_top_level_empty"
    if not isinstance(rejected_field, str) or not rejected_field.strip():
        return False, "rejected_top_level_empty"

    if not chosen_text:
        return False, "chosen_empty"
    if not isinstance(messages.get("chosen"), list):
        return False, "chosen_messages_invalid"
    if not isinstance(messages.get("rejected"), list):
        return False, "rejected_messages_invalid"
    if not isinstance(messages.get("user"), list):
        return False, "user_messages_invalid"

    flat_user = row.get("messages_flat", {}).get("user")
    flat_chosen = row.get("messages_flat", {}).get("chosen")
    if isinstance(flat_user, str) and flat_user.strip() != user_text.strip():
        return False, "messages_flat_user_mismatch"
    if isinstance(flat_chosen, str) and flat_chosen.strip() != chosen_text.strip():
        return False, "messages_flat_chosen_mismatch"

    if _identity_hit_fail(chosen_text):
        return False, "identity_drift"

    forbidden = _forbidden_hit(chosen_text)
    if forbidden:
        return False, f"forbidden:{forbidden}"

    try:
        chosen_score = float(row.get("chosen_score"))
        rejected_score = float(row.get("rejected_score"))
        margin = float(row.get("margin"))
    except (TypeError, ValueError):
        return False, "score_invalid"

    if chosen_score <= rejected_score:
        return False, "margin_invalid"
    if margin < 0.8:
        return False, "margin_too_low"

    failure_modes = row.get("failure_modes")
    if not isinstance(failure_modes, list) or not failure_modes:
        return False, "failure_modes_missing"
    bad_modes = [m for m in failure_modes if m not in ALLOWED_FAILURE_MODES]
    if bad_modes:
        return False, f"failure_mode_not_allowed:{','.join(sorted(set(bad_modes)))}"

    sig = signature_prompt_assistant(user_text, chosen_text)
    if sig in seen_sigs:
        return False, "exact_duplicate"

    seen_ids.add(row_id)
    seen_sigs.add(sig)
    return True, ""


def run_generator(args: argparse.Namespace) -> ReviewResult:
    cfg = load_or_prepare_config(Path(args.config))
    output_root = Path(args.output_root).resolve()
    chunks_dir = output_root / "chunks"

    prefix = f"{args.run_id}-chunk-{args.chunk_id:04d}-{args.shard_id}"
    rng = random.Random(args.random_seed)
    builder = IdentityDatasetBuilder(cfg, rng, args.run_id, output_root)

    seeds = build_shard_seeds(
        cfg=cfg,
        rng=rng,
        seed_count=args.seed_count,
        seed_prefix=prefix,
    )

    rows = builder.generate_sft_rows(seeds, args.target_sft_shard)
    pairs = builder.generate_preference_pairs(rows, args.target_pref_shard)

    if len(rows) < args.target_sft_shard:
        return ReviewResult(False, f"insufficient_sft_rows:{len(rows)}<{args.target_sft_shard}")
    if len(pairs) < args.target_pref_shard:
        return ReviewResult(False, f"insufficient_pref_rows:{len(pairs)}<{args.target_pref_shard}")

    rows = rows[: args.target_sft_shard]
    pairs = pairs[: args.target_pref_shard]

    for idx, row in enumerate(rows, start=1):
        row["id"] = f"identity-sft-{args.chunk_id:04d}-{args.shard_id}-{idx:07d}"
        row["run_id"] = args.run_id

    for idx, row in enumerate(pairs, start=1):
        row["id"] = f"identity-pref-{args.chunk_id:04d}-{args.shard_id}-{idx:07d}"
        row["run_id"] = args.run_id

    pending_sft = chunks_dir / "pending" / f"sft_chunk_{args.chunk_id:04d}_{args.shard_id}.jsonl"
    pending_pref = chunks_dir / "pending" / f"pref_chunk_{args.chunk_id:04d}_{args.shard_id}.jsonl"
    write_jsonl(pending_sft, rows)
    write_jsonl(pending_pref, pairs)

    meta = {
        "run_id": args.run_id,
        "chunk_id": args.chunk_id,
        "shard_id": args.shard_id,
        "sft_rows": len(rows),
        "pref_rows": len(pairs),
        "candidate_evaluations": builder.total_candidates,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "target_sft_shard": args.target_sft_shard,
        "target_pref_shard": args.target_pref_shard,
        "seed": args.random_seed,
    }
    write_json(chunks_dir / "pending" / f"meta_chunk_{args.chunk_id:04d}_{args.shard_id}.json", meta)

    return ReviewResult(
        True,
        (
            f"GEN_COMPLETE run_id={args.run_id} "
            f"chunk_id={args.chunk_id} shard={args.shard_id} "
            f"sft={len(rows)} pref={len(pairs)}"
        ),
        approved_sft=len(rows),
        approved_pref=len(pairs),
    )


def run_review(args: argparse.Namespace) -> ReviewResult:
    output_root = Path(args.output_root).resolve()
    chunks_dir = output_root / "chunks"
    reviewed_dir = chunks_dir / "reviewed"
    reviewed_dir.mkdir(parents=True, exist_ok=True)

    if args.review_target in {"gen_a", "gen_b"}:
        sft_in = chunks_dir / "pending" / f"sft_chunk_{args.chunk_id:04d}_{args.review_target}.jsonl"
        pref_in = chunks_dir / "pending" / f"pref_chunk_{args.chunk_id:04d}_{args.review_target}.jsonl"
        sft_out = reviewed_dir / f"sft_chunk_{args.chunk_id:04d}_{args.review_target}.approved.jsonl"
        pref_out = reviewed_dir / f"pref_chunk_{args.chunk_id:04d}_{args.review_target}.approved.jsonl"

        rows_sft, bad_sft, err_sft = read_jsonl(sft_in)
        rows_pref, bad_pref, err_pref = read_jsonl(pref_in)

        if bad_sft or bad_pref:
            return ReviewResult(False, f"invalid_json:{err_sft or err_pref}")

        reviewed_sft: List[Dict[str, Any]] = []
        reviewed_pref: List[Dict[str, Any]] = []
        seen_ids: set = set()
        seen_sigs: set = set()

        for row in rows_sft:
            ok, reason = validate_sft_row(row, args.run_id, seen_ids, seen_sigs)
            if ok:
                reviewed_sft.append(row)
            else:
                # row-level rejections are intentionally accepted if rejected silently for now.
                pass

        seen_ids = set()
        seen_sigs = set()
        for row in rows_pref:
            ok, reason = validate_pref_row(row, args.run_id, seen_ids, seen_sigs)
            if ok:
                reviewed_pref.append(row)
            else:
                pass

        report = {
            "run_id": args.run_id,
            "chunk_id": args.chunk_id,
            "review_target": args.review_target,
            "status": "approved",
            "approved_sft": len(reviewed_sft),
            "approved_pref": len(reviewed_pref),
            "total_input_sft": len(rows_sft),
            "total_input_pref": len(rows_pref),
            "invalid_lines_sft": bad_sft,
            "invalid_lines_pref": bad_pref,
        }

        write_jsonl(sft_out, reviewed_sft)
        write_jsonl(pref_out, reviewed_pref)
        write_json(reviewed_dir / f"review_{args.review_target}_chunk_{args.chunk_id:04d}.json", report)

        # Keep required policy: reject if approved volume below target.
        if len(reviewed_sft) < args.target_sft_shard or len(reviewed_pref) < args.target_pref_shard:
            return ReviewResult(
                False,
                f"insufficient_approved:{len(reviewed_sft)}/{len(reviewed_pref)} "
                f"<{args.target_sft_shard}/{args.target_pref_shard}",
                approved_sft=len(reviewed_sft),
                approved_pref=len(reviewed_pref),
            )

        return ReviewResult(
            True,
            (
                f"REVIEW_COMPLETE run_id={args.run_id} chunk_id={args.chunk_id} target={args.review_target} "
                f"approved_sft={len(reviewed_sft)} approved_pref={len(reviewed_pref)}"
            ),
            approved_sft=len(reviewed_sft),
            approved_pref=len(reviewed_pref),
        )

    if args.review_target == "merge":
        sft_in = chunks_dir / f"sft_chunk_{args.chunk_id:04d}.tmp.jsonl"
        pref_in = chunks_dir / f"pref_chunk_{args.chunk_id:04d}.tmp.jsonl"
        rows_sft, bad_sft, err_sft = read_jsonl(sft_in)
        rows_pref, bad_pref, err_pref = read_jsonl(pref_in)

        if bad_sft or bad_pref:
            return ReviewResult(False, f"invalid_json:{err_sft or err_pref}")

        if len(rows_sft) < args.target_sft_shard:
            return ReviewResult(False, f"insufficient_sft:{len(rows_sft)}<{args.target_sft_shard}")
        if len(rows_pref) < args.target_pref_shard:
            return ReviewResult(False, f"insufficient_pref:{len(rows_pref)}<{args.target_pref_shard}")

        seen_ids: set = set()
        seen_sigs: set = set()
        for row in rows_sft:
            ok, reason = validate_sft_row(row, args.run_id, seen_ids, seen_sigs)
            if not ok:
                return ReviewResult(False, f"sft_block:{reason}")

        seen_ids = set()
        seen_sigs = set()
        for row in rows_pref:
            ok, reason = validate_pref_row(row, args.run_id, seen_ids, seen_sigs)
            if not ok:
                return ReviewResult(False, f"pref_block:{reason}")

        output = {
            "run_id": args.run_id,
            "chunk_id": args.chunk_id,
            "review_target": "merge",
            "status": "approved",
            "sft_rows": len(rows_sft),
            "pref_rows": len(rows_pref),
            "invalid_lines_sft": bad_sft,
            "invalid_lines_pref": bad_pref,
        }
        write_json(reviewed_dir / f"review_merge_chunk_{args.chunk_id:04d}.json", output)
        return ReviewResult(
            True,
            f"REVIEW_COMPLETE run_id={args.run_id} chunk_id={args.chunk_id} target=merge approved=true",
            approved_sft=len(rows_sft),
            approved_pref=len(rows_pref),
        )

    if args.review_target in {"final_sft", "final_pref", "final_report"}:
        review_dir = output_root / "review_logs"
        review_dir.mkdir(parents=True, exist_ok=True)

        if args.review_target == "final_sft":
            input_path = output_root / "sft_dataset.jsonl"
            rows, bad, err = read_jsonl(input_path)
            if bad:
                return ReviewResult(False, f"invalid_json:{err}")

            seen_ids: set = set()
            seen_sigs: set = set()
            for row in rows:
                ok, reason = validate_sft_row(row, args.run_id, seen_ids, seen_sigs)
                if not ok:
                    return ReviewResult(False, f"sft_block:{reason}")

            output = {
                "run_id": args.run_id,
                "chunk_id": args.chunk_id,
                "review_target": "final_sft",
                "status": "approved",
                "total_rows": len(rows),
                "invalid_lines": bad,
            }
            write_json(review_dir / "review_final_sft.json", output)
            return ReviewResult(
                True,
                f"REVIEW_COMPLETE run_id={args.run_id} chunk_id={args.chunk_id} target=final_sft approved=true",
                approved_sft=len(rows),
            )

        if args.review_target == "final_pref":
            input_path = output_root / "preference_dataset.jsonl"
            rows, bad, err = read_jsonl(input_path)
            if bad:
                return ReviewResult(False, f"invalid_json:{err}")

            seen_ids: set = set()
            seen_sigs: set = set()
            for row in rows:
                ok, reason = validate_pref_row(row, args.run_id, seen_ids, seen_sigs)
                if not ok:
                    return ReviewResult(False, f"pref_block:{reason}")

            output = {
                "run_id": args.run_id,
                "chunk_id": args.chunk_id,
                "review_target": "final_pref",
                "status": "approved",
                "total_rows": len(rows),
                "invalid_lines": bad,
            }
            write_json(review_dir / "review_final_pref.json", output)
            return ReviewResult(
                True,
                f"REVIEW_COMPLETE run_id={args.run_id} chunk_id={args.chunk_id} target=final_pref approved=true",
                approved_pref=len(rows),
            )

        report_path = output_root / "review_report.json"
        cat_path = output_root / "category_manifest.json"
        lang_path = output_root / "language_manifest.json"
        mm_path = output_root / "multimodal_manifest.json"

        for p in [report_path, cat_path, lang_path, mm_path]:
            if not p.exists():
                return ReviewResult(False, f"missing_artifact:{p.name}")

        try:
            with report_path.open("r", encoding="utf-8") as f:
                report_payload = json.load(f)
            with cat_path.open("r", encoding="utf-8") as f:
                cat_payload = json.load(f)
            with lang_path.open("r", encoding="utf-8") as f:
                lang_payload = json.load(f)
            with mm_path.open("r", encoding="utf-8") as f:
                mm_payload = json.load(f)
        except Exception as exc:  # pragma: no cover
            return ReviewResult(False, f"invalid_json:{exc}")

        if report_payload.get("run_id") != args.run_id:
            return ReviewResult(False, "run_id_mismatch")
        if report_payload.get("status") != "completed":
            return ReviewResult(False, "report_status_invalid")
        counts = report_payload.get("counts")
        if not isinstance(counts, dict):
            return ReviewResult(False, "report_counts_missing")
        if not isinstance(counts.get("sft_rows_generated"), int) or not isinstance(
            counts.get("preference_pairs_generated"), int
        ):
            return ReviewResult(False, "report_counts_invalid")
        if not report_payload.get("within_targets", False):
            return ReviewResult(False, "report_within_targets_false")
        if not isinstance(report_payload.get("quality_warnings"), list):
            return ReviewResult(False, "report_quality_warnings_missing")

        if not isinstance(cat_payload.get("category_breakdown"), dict):
            return ReviewResult(False, "category_manifest_missing")
        if cat_payload.get("type") != "category_manifest":
            return ReviewResult(False, "category_manifest_type_invalid")
        if not isinstance(lang_payload.get("language_breakdown"), dict):
            return ReviewResult(False, "language_manifest_missing")
        if lang_payload.get("type") != "language_manifest":
            return ReviewResult(False, "language_manifest_type_invalid")
        if not isinstance(mm_payload.get("multimodal_breakdown"), dict):
            return ReviewResult(False, "multimodal_manifest_missing")
        if mm_payload.get("type") != "multimodal_manifest":
            return ReviewResult(False, "multimodal_manifest_type_invalid")

        output = {
            "run_id": args.run_id,
            "chunk_id": args.chunk_id,
            "review_target": "final_report",
            "status": "approved",
        }
        write_json(review_dir / "review_final_report.json", output)
        return ReviewResult(
            True,
            f"REVIEW_COMPLETE run_id={args.run_id} chunk_id={args.chunk_id} target=final_report approved=true",
        )

    return ReviewResult(False, f"unsupported_target:{args.review_target}")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Codex chunk worker")
    p.add_argument(
        "--config",
        default=str(Path(__file__).with_name("config") / "identity_dataset_config.json"),
    )
    p.add_argument(
        "--policy",
        default=str(Path(__file__).parent.parent / "lumis1_identity_codex_prompt.txt"),
    )
    p.add_argument(
        "--output-root",
        default=str(Path(__file__).parent / "output" / "full_run_codex_spark_xhigh"),
    )
    p.add_argument("--run-id", required=True)
    p.add_argument("--chunk-id", type=int, required=True)
    p.add_argument("--shard-id", choices=["gen_a", "gen_b"], default="gen_a")
    p.add_argument("--target-sft-shard", type=int, required=True)
    p.add_argument("--target-pref-shard", type=int, required=True)
    p.add_argument("--random-seed", type=int, default=3407)
    p.add_argument("--seed-count", type=int, default=2200)
    p.add_argument(
        "--review-target",
        choices=["gen_a", "gen_b", "merge", "final_sft", "final_pref", "final_report"],
        default="gen_a",
    )
    p.add_argument("--mode", choices=["generator", "reviewer"], required=True)
    return p.parse_args(argv)


def main(argv: Sequence[str]) -> int:
    args = parse_args(argv)

    if not args.run_id or not args.run_id.startswith("identity-"):
        print(
            f"GEN_PAUSED run_id={args.run_id} chunk_id={args.chunk_id} "
            f"shard={args.shard_id if args.mode == 'generator' else args.review_target} reason=invalid_run_id"
        )
        return 1

    if args.mode == "generator":
        result = run_generator(args)
    else:
        result = run_review(args)

    if result.message:
        print(result.message)

    if result.ok:
        return 0

    if args.mode == "generator":
        print(
            f"GEN_PAUSED run_id={args.run_id} chunk_id={args.chunk_id} shard={args.shard_id} "
            f"reason={result.message}"
        )
    else:
        target = args.review_target
        print(
            f"REVIEW_BLOCKED run_id={args.run_id} chunk_id={args.chunk_id} "
            f"target={target} reason={result.message}"
        )
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
