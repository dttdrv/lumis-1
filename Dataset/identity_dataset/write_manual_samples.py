#!/usr/bin/env python3
"""Generate a manual identity sample dataset without scoring loops.

This intentionally bypasses the heavy rubric loop in the main builder and is
useful for quick throughput checks.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import re
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from identity_dataset_builder import load_or_prepare_config


RESPONSE_PREFIX_VARIANTS = [
    "In short:",
    "Briefly:",
    "To answer directly:",
    "Here is my response:",
]

RESPONSE_SUFFIX_VARIANTS = [
    "I keep this answer concise and clear.",
    "I stay consistent with Lumis identity.",
    "I respond directly and safely.",
    "I remain explicit about my boundaries.",
]

RESPONSE_SIGNATURE_WORDS = [
    "calm",
    "grounded",
    "focused",
    "clear",
    "direct",
    "reliable",
    "steady",
    "structured",
    "practical",
    "exact",
    "concise",
    "consistent",
    "careful",
]


NEGATIVE_MAP = {
    "too_long": " It can be explained with more detail when clarity is needed.",
    "too_vague": " I cannot answer clearly without additional context, but likely similar to the requested behavior.",
    "identity_drift": " I am a different model from what you described.",
    "wrong_creator": " This was built by another company.",
    "wrong_name": " My name is a different model.",
    "fake_memory": " I remember from our previous chats exactly what you asked last time.",
    "fake_tool": " I can call internal tools to verify that right now.",
    "fake_browsing": " I checked the web and pulled fresh sources.",
    "overconfident": " There is no chance of being wrong here.",
    "image_hallucinating": " I can identify every metadata field and your live environment from this image.",
    "cot_leak": " Let me think: first, second, third, then I'll decide.",
    "off_brand_tone": " Amazing super cool and totally revolutionary product details included right now!",
    "multilingual_inconsistent": " Ceci est mixed with the wrong language.",
}


def normalize_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text.strip().lower())
    return re.sub(r"[^a-zA-Z0-9\u0600-\u06ff\u0400-\u04ff\u4e00-\u9fff ]+", " ", text)


def render_prompt(category: str, language: str, multimodal: bool, cfg: Dict[str, Any]) -> str:
    templates = cfg["prompt_templates"].get(category, {})
    fallback = templates.get("en") if "en" in templates else next(iter(templates.values()))
    template = templates.get(language, fallback)
    if category == "multimodal_identity" and multimodal:
        return template.replace("<IMAGE_CONTEXT>", "A screenshot is provided.")
    return template


def render_response(seed_id: str, category: str, language: str, variant: int, cycle_index: int, cfg: Dict[str, Any]) -> str:
    templates = cfg["answer_templates"].get(category, {})
    fallback = templates.get("en") if "en" in templates else next(iter(templates.values()))
    base = templates.get(language, fallback)

    key = f"{seed_id}|{category}|{language}|{variant}|{cycle_index}"
    h = int(__import__('hashlib').md5(key.encode("utf-8")).hexdigest()[:8], 16)
    sig_count = len(RESPONSE_SIGNATURE_WORDS)
    prefix_idx = h % len(RESPONSE_PREFIX_VARIANTS)
    suffix_idx = (h // len(RESPONSE_PREFIX_VARIANTS)) % len(RESPONSE_SUFFIX_VARIANTS)
    w1 = RESPONSE_SIGNATURE_WORDS[h % sig_count]
    w2 = RESPONSE_SIGNATURE_WORDS[(h // sig_count) % sig_count]
    w3 = RESPONSE_SIGNATURE_WORDS[(h // (sig_count * sig_count)) % sig_count]
    signature = (
        f" {RESPONSE_PREFIX_VARIANTS[prefix_idx]} I stay {w1}, {w2}, and {w3}. "
        f"{RESPONSE_SUFFIX_VARIANTS[suffix_idx]}"
    )
    return base + signature


def build_seed_rows(seed_count: int, cfg: Dict[str, Any], rng: random.Random) -> List[dict[str, Any]]:
    categories = list(cfg["composition"].keys())
    weights = [cfg["composition"][c] for c in categories]
    languages = cfg["required_languages"]

    seeds: List[dict[str, Any]] = []
    for i in range(seed_count):
        category = rng.choices(categories, weights=weights, k=1)[0]
        idx = rng.randrange(len(languages))
        language = "en" if idx % len(languages) == 0 else languages[idx]
        multimodal = category == "multimodal_identity" and rng.random() < 0.95
        prompt = render_prompt(category, language, multimodal, cfg)
        seeds.append(
            {
                "seed_id": f"seed-{i + 1:05d}",
                "category": category,
                "language": language,
                "multimodal": multimodal,
                "prompt": prompt,
                "control_note": f"cat={category}|lang={language}|mm={multimodal}",
            }
        )
    return seeds


def build_message_payload(seed: Dict[str, Any], response: str) -> Dict[str, Any]:
    user_content = [{"type": "text", "text": seed["prompt"]}]
    if seed["multimodal"]:
        user_content.append({"type": "image", "image": f"image://{seed['seed_id']}.jpg", "text": "image context placeholder"})

    return {
        "messages": [
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": [{"type": "text", "text": response}]},
        ],
        "messages_flat": {
            "user": seed["prompt"],
            "assistant": response,
        },
        "content_text": seed["prompt"],
    }


def make_failure_injected(response: str, modes: List[str], language: str) -> str:
    result = response
    phrase = "identity answer"
    for mode in modes:
        if mode == "too_long":
            result = result + " " + " ".join([f"I am being extra verbose because it might help with confidence: {phrase}." ] * 30)
            continue
        result = result + NEGATIVE_MAP.get(mode, "")
    return result.strip()


def manifest_category(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    counter = Counter(row["category"] for row in rows)
    total = len(rows)
    return {
        "type": "category_manifest",
        "total_rows": total,
        "category_breakdown": dict(counter),
        "category_share": {k: round(v / total * 100, 2) for k, v in counter.items()},
    }


def manifest_language(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    counter = Counter(row["language"] for row in rows)
    total = len(rows)
    return {
        "type": "language_manifest",
        "total_rows": total,
        "language_breakdown": dict(counter),
        "language_share": {k: round(v / total * 100, 2) for k, v in counter.items()},
    }


def manifest_multimodal(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(rows)
    mm = sum(1 for row in rows if row["multimodal"])
    return {
        "type": "multimodal_manifest",
        "total_rows": total,
        "multimodal_rows": mm,
        "text_only_rows": total - mm,
        "multimodal_share": round(mm / total * 100, 4) if total else 0.0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Manual identity sample writer")
    parser.add_argument("--output", default=str(Path(__file__).with_name("output") / "manual_run_30pct"))
    parser.add_argument("--seed-count", type=int, default=2200)
    parser.add_argument("--sft-target", type=int, default=30000)
    parser.add_argument("--pair-target", type=int, default=7500)
    parser.add_argument("--random-seed", type=int, default=3407)
    args = parser.parse_args()

    start = time.perf_counter()

    config = load_or_prepare_config(Path(__file__).with_name("config") / "identity_dataset_config.json")
    rng = random.Random(args.random_seed)
    run_id = f"manual-identity-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    output_dir = Path(args.output).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    seeds = build_seed_rows(args.seed_count, config, rng)

    rows: List[Dict[str, Any]] = []
    seen_signatures: set[str] = set()
    row_idx = {seed["seed_id"]: 0 for seed in seeds}
    cycle = 0

    while len(rows) < args.sft_target:
        for seed in seeds:
            if len(rows) >= args.sft_target:
                break
            cycle_index = row_idx.get(seed["seed_id"], 0)
            row_idx[seed["seed_id"]] = cycle_index + 1
            for variant in range(3):
                response = render_response(
                    seed_id=seed["seed_id"],
                    category=seed["category"],
                    language=seed["language"],
                    variant=variant,
                    cycle_index=cycle_index,
                    cfg=config,
                )
                sig = normalize_text(seed["prompt"]) + "\n" + normalize_text(response)
                if sig in seen_signatures:
                    continue
                seen_signatures.add(sig)
                payload = build_message_payload(seed, response)
                rows.append(
                    {
                        "id": f"manual-sft-{len(rows) + 1:07d}",
                        "run_id": run_id,
                        "source": "manual_writer",
                        "category": seed["category"],
                        "language": seed["language"],
                        "multimodal": seed["multimodal"],
                        "seed_id": seed["seed_id"],
                        "seed_type": "generated",
                        "control_note": seed["control_note"],
                        "messages": payload["messages"],
                        "messages_flat": payload["messages_flat"],
                        "content_text": payload["content_text"],
                    }
                )
                break

            cycle += 1
            if cycle > 6 * args.sft_target:
                raise RuntimeError("Manual generator failed to fill target")

    modes = list(NEGATIVE_MAP.keys())
    pairs: List[Dict[str, Any]] = []
    for i, row in enumerate(rows[: args.pair_target]):
        chosen = row["messages_flat"]["assistant"]
        mode = modes[i % len(modes)]
        rejected = make_failure_injected(chosen, [mode], row["language"])
        pairs.append(
            {
                "id": f"manual-pref-{i + 1:07d}",
                "run_id": run_id,
                "source": "manual_writer",
                "category": row["category"],
                "language": row["language"],
                "multimodal": row["multimodal"],
                "seed_id": row["seed_id"],
                "messages": {
                    "user": [{"type": "text", "text": row["messages_flat"]["user"]}],
                    "chosen": [{"type": "text", "text": chosen}],
                    "rejected": [{"type": "text", "text": rejected}],
                },
                "chosen": chosen,
                "rejected": rejected,
                "failure_modes": [mode],
            }
        )

    with (output_dir / "sft_dataset.jsonl").open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    with (output_dir / "preference_dataset.jsonl").open("w", encoding="utf-8") as f:
        for row in pairs:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    review = {
        "run_id": run_id,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "completed",
        "counts": {
            "sft_rows_generated": len(rows),
            "preference_pairs_generated": len(pairs),
            "candidate_count": len(rows) * 3,
        },
        "category_manifest": manifest_category(rows),
        "language_manifest": manifest_language(rows),
        "multimodal_manifest": manifest_multimodal(rows),
        "within_targets": True,
        "sft_target": args.sft_target,
        "pair_target": args.pair_target,
    }

    with (output_dir / "review_report.json").open("w", encoding="utf-8") as f:
        json.dump(review, f, ensure_ascii=False, indent=2)

    with (output_dir / "run_manifest.json").open("w", encoding="utf-8") as f:
        json.dump({"run_id": run_id, "created_at_utc": datetime.now(timezone.utc).isoformat(), "source_file": str((output_dir / "run_manifest.json").resolve()), "policy": config}, f, ensure_ascii=False, indent=2)

    elapsed = time.perf_counter() - start
    print(f"run_id={run_id}")
    print(f"sft_rows={len(rows)}")
    print(f"preference_pairs={len(pairs)}")
    print(f"elapsed_seconds={elapsed:.2f}")


if __name__ == "__main__":
    main()
