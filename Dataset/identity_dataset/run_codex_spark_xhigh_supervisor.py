#!/usr/bin/env python3
"""Autonomous chunk supervisor for Codex Spark xhigh identity dataset generation."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import math
import random
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from identity_dataset_builder import load_or_prepare_config, IdentityDatasetBuilder


ROOT = Path(__file__).resolve().parent
OUTPUT_ROOT = ROOT / "output" / "full_run_codex_spark_xhigh"
CONFIG_PATH = ROOT / "config" / "identity_dataset_config.json"
POLICY_PATH = ROOT.parent / "lumis1_identity_codex_prompt.txt"
MANUAL_WRITER_PATH = ROOT / "write_manual_samples.py"
WORKER_PATH = ROOT / "codex_chunk_worker.py"

TARGET_SFT = 100_000
TARGET_PREF = 25_000


DEFAULT_STATE: Dict[str, Any] = {
    "run_id": "identity-<UTCSTAMP>",
    "status": "active",
    "next_chunk": 1,
    "sft_written": 0,
    "pref_written": 0,
    "target_sft": TARGET_SFT,
    "target_pref": TARGET_PREF,
    "chunk_sft": 1000,
    "chunk_pref": 250,
    "chunk_sft_min": 125,
    "chunk_pref_min": 32,
    "consecutive_failures": 0,
    "updated_at_utc": "",
}



def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text.strip().lower())
    text = re.sub(r"[^a-zA-Z0-9\u0600-\u06ff\u0400-\u04ff\u4e00-\u9fff ]+", " ", text)
    return text


def exact_signature(prompt: str, assistant: str) -> str:
    payload = f"{normalize_text(prompt)}\n{normalize_text(assistant)}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def signature_pref(prompt: str, chosen: str) -> str:
    return exact_signature(prompt, chosen)


def extract_sft_signature(row: Dict[str, Any]) -> Tuple[str, str]:
    prompt = ""
    assistant = ""
    if isinstance(row, dict):
        messages = row.get("messages")
        if isinstance(messages, list) and len(messages) >= 2:
            user_msg = messages[0]
            asst_msg = messages[1]
            if isinstance(user_msg, dict):
                content = user_msg.get("content")
                if isinstance(content, list):
                    prompt = " ".join(
                        str(part.get("text", ""))
                        for part in content
                        if isinstance(part, dict) and isinstance(part.get("text"), str)
                    ).strip()
                elif isinstance(user_msg.get("content_text"), str):
                    prompt = user_msg.get("content_text", "")
            if isinstance(asst_msg, dict):
                content = asst_msg.get("content")
                if isinstance(content, list):
                    assistant = " ".join(
                        str(part.get("text", ""))
                        for part in content
                        if isinstance(part, dict) and isinstance(part.get("text"), str)
                    ).strip()
                elif isinstance(asst_msg.get("content_text"), str):
                    assistant = asst_msg.get("content_text", "")
    if not prompt and isinstance(row, dict) and isinstance(row.get("messages_flat"), dict):
        prompt = row.get("messages_flat", {}).get("user", prompt)
    if not assistant and isinstance(row, dict) and isinstance(row.get("messages_flat"), dict):
        assistant = row.get("messages_flat", {}).get("assistant", assistant)
    return str(prompt), str(assistant)


def extract_pref_signature(row: Dict[str, Any]) -> Tuple[str, str]:
    prompt = ""
    chosen = ""
    if isinstance(row, dict):
        messages = row.get("messages")
        if isinstance(messages, dict):
            user_msg = messages.get("user")
            chosen_msg = messages.get("chosen")
            if isinstance(user_msg, list):
                prompt = " ".join(
                    str(part.get("text", ""))
                    for part in user_msg
                    if isinstance(part, dict) and isinstance(part.get("text"), str)
                ).strip()
            if isinstance(chosen_msg, list):
                chosen = " ".join(
                    str(part.get("text", ""))
                    for part in chosen_msg
                    if isinstance(part, dict) and isinstance(part.get("text"), str)
                ).strip()
        if not prompt and isinstance(row.get("messages_flat"), dict):
            prompt = row.get("messages_flat", {}).get("user", prompt)
        if not chosen and isinstance(row.get("messages_flat"), dict):
            chosen = row.get("messages_flat", {}).get("chosen", chosen)
    return str(prompt), str(chosen)


def safe_read_jsonl(path: Path) -> Tuple[List[Dict[str, Any]], int]:
    rows: List[Dict[str, Any]] = []
    if not path.exists():
        return rows, 1

    bad = 0
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                bad += 1
    return rows, bad


def write_jsonl(path: Path, rows: Sequence[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def atomic_write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def load_state(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def bootstrap_state(config: Dict[str, Any]) -> Dict[str, Any]:
    state_path = OUTPUT_ROOT / "state.json"
    run_id = f"identity-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    is_new_run = not state_path.exists()

    if not state_path.exists():
        if OUTPUT_ROOT.exists():
            # brand-new run should start clean.
            shutil.rmtree(OUTPUT_ROOT)
        OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
        state = DEFAULT_STATE.copy()
        state["run_id"] = run_id
        state["updated_at_utc"] = now_utc()
        atomic_write_json(state_path, state)
    state = load_state(state_path)

    # ensure required structure
    for key, value in DEFAULT_STATE.items():
        state.setdefault(key, value)

    state.setdefault("run_id", run_id)
    state.setdefault("status", "active")
    state.setdefault("target_sft", TARGET_SFT)
    state.setdefault("target_pref", TARGET_PREF)

    state["target_sft"] = TARGET_SFT
    state["target_pref"] = TARGET_PREF

    # ensure bootstrap contracts
    state["chunk_sft"] = state.get("chunk_sft", 1000)
    state["chunk_pref"] = state.get("chunk_pref", 250)
    state["chunk_sft_min"] = state.get("chunk_sft_min", 125)
    state["chunk_pref_min"] = state.get("chunk_pref_min", 32)
    state["consecutive_failures"] = int(state.get("consecutive_failures", 0))
    state["updated_at_utc"] = now_utc()

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    (OUTPUT_ROOT / "chunks").mkdir(parents=True, exist_ok=True)
    (OUTPUT_ROOT / "chunks" / "pending").mkdir(parents=True, exist_ok=True)
    (OUTPUT_ROOT / "chunks" / "reviewed").mkdir(parents=True, exist_ok=True)
    (OUTPUT_ROOT / "review_logs").mkdir(parents=True, exist_ok=True)

    # make sure exact dedupe file exists
    dedupe_file = OUTPUT_ROOT / "dedupe_exact.sha256.txt"
    if not dedupe_file.exists():
        dedupe_file.write_text("", encoding="utf-8")
    if is_new_run:
        dedupe_file.write_text("", encoding="utf-8")

    heartbeat = OUTPUT_ROOT / "heartbeat.log"
    if not heartbeat.exists():
        heartbeat.write_text("", encoding="utf-8")

    atomic_write_json(state_path, state)
    return state


def append_heartbeat(state: Dict[str, Any]) -> None:
    heartbeat = OUTPUT_ROOT / "heartbeat.log"
    rec = {
        "utc": now_utc(),
        "run_id": state["run_id"],
        "status": state["status"],
        "next_chunk": state["next_chunk"],
        "sft_written": state["sft_written"],
        "pref_written": state["pref_written"],
        "consecutive_failures": state["consecutive_failures"],
    }
    with heartbeat.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def read_dedupe_set() -> set[str]:
    file_path = OUTPUT_ROOT / "dedupe_exact.sha256.txt"
    if not file_path.exists():
        return set()
    rows = file_path.read_text(encoding="utf-8").splitlines()
    return set(r.strip() for r in rows if r.strip())


def append_dedupe_signatures(signatures: Sequence[str]) -> None:
    if not signatures:
        return
    dedupe_file = OUTPUT_ROOT / "dedupe_exact.sha256.txt"
    with dedupe_file.open("a", encoding="utf-8") as f:
        for sig in signatures:
            f.write(f"{sig}\n")


def cleanup_chunk(chunk_id: int) -> None:
    chunk_dir = OUTPUT_ROOT / "chunks"
    chunk_idx = f"{chunk_id:04d}"
    for shard in ("gen_a", "gen_b"):
        for name in [
            chunk_dir / "pending" / f"sft_chunk_{chunk_idx}_{shard}.jsonl",
            chunk_dir / "pending" / f"pref_chunk_{chunk_idx}_{shard}.jsonl",
            chunk_dir / "pending" / f"meta_chunk_{chunk_idx}_{shard}.json",
            chunk_dir / "reviewed" / f"sft_chunk_{chunk_idx}_{shard}.approved.jsonl",
            chunk_dir / "reviewed" / f"pref_chunk_{chunk_idx}_{shard}.approved.jsonl",
            chunk_dir / "reviewed" / f"review_{shard}_chunk_{chunk_idx}.json",
        ]:
            if name.exists():
                try:
                    name.unlink()
                except Exception:
                    pass
    for path in [
        chunk_dir / f"sft_chunk_{chunk_idx}.tmp.jsonl",
        chunk_dir / f"pref_chunk_{chunk_idx}.tmp.jsonl",
        chunk_dir / f"sft_chunk_{chunk_idx}.jsonl",
        chunk_dir / f"pref_chunk_{chunk_idx}.jsonl",
    ]:
        if path.exists():
            try:
                path.unlink()
            except Exception:
                pass


def pending_rows_valid(
    chunk_id: int,
    shard: str,
    target_sft: int,
    target_pref: int,
    run_id: str,
) -> bool:
    chunk_idx = f"{chunk_id:04d}"
    base = OUTPUT_ROOT / "chunks" / "pending"
    sft_path = base / f"sft_chunk_{chunk_idx}_{shard}.jsonl"
    pref_path = base / f"pref_chunk_{chunk_idx}_{shard}.jsonl"

    sft_rows, sft_bad = safe_read_jsonl(sft_path)
    pref_rows, pref_bad = safe_read_jsonl(pref_path)
    if sft_bad or pref_bad:
        return False

    if not sft_rows or not pref_rows:
        return False

    if len(sft_rows) < target_sft or len(pref_rows) < target_pref:
        return False

    seen_ids = set()
    for row in sft_rows[:target_sft]:
        if not isinstance(row, dict):
            return False
        if row.get("run_id") != run_id or not isinstance(row.get("id"), str):
            return False
        if row["id"] in seen_ids:
            return False
        seen_ids.add(row["id"])

    seen_ids = set()
    for row in pref_rows[:target_pref]:
        if not isinstance(row, dict):
            return False
        if row.get("run_id") != run_id or not isinstance(row.get("id"), str):
            return False
        if row["id"] in seen_ids:
            return False
        seen_ids.add(row["id"])

    return True


def call_worker(args: List[str], timeout: int = 1200) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, *args],
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )


def run_generator(run_id: str, chunk_id: int, shard: str, target_sft: int, target_pref: int, seed: int) -> Tuple[bool, str]:
    cmd = [
        str(WORKER_PATH),
        "--mode",
        "generator",
        "--config",
        str(CONFIG_PATH),
        "--run-id",
        run_id,
        "--chunk-id",
        str(chunk_id),
        "--shard-id",
        shard,
        "--target-sft-shard",
        str(target_sft),
        "--target-pref-shard",
        str(target_pref),
        "--random-seed",
        str(seed),
        "--seed-count",
        "2200",
        "--output-root",
        str(OUTPUT_ROOT),
    ]
    proc = call_worker(cmd)
    ok = proc.returncode == 0
    return ok, (proc.stdout or "").strip() + (proc.stderr or "")


def run_reviewer(args: Dict[str, Any]) -> Tuple[bool, str]:
    cmd = [
        str(WORKER_PATH),
        "--mode",
        "reviewer",
        "--config",
        str(CONFIG_PATH),
        "--run-id",
        args["run_id"],
        "--chunk-id",
        str(args["chunk_id"]),
        "--review-target",
        args["target"],
        "--target-sft-shard",
        str(args["target_sft_shard"]),
        "--target-pref-shard",
        str(args["target_pref_shard"]),
        "--output-root",
        str(OUTPUT_ROOT),
    ]
    proc = call_worker(cmd)
    ok = proc.returncode == 0
    return ok, (proc.stdout or "").strip() + (proc.stderr or "")


def load_chunk_rows(
    chunk_id: int,
    shard: str,
    target_sft: int,
    target_pref: int,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    idx = f"{chunk_id:04d}"
    reviewed = OUTPUT_ROOT / "chunks" / "reviewed"
    sft_rows, bad_sft = safe_read_jsonl(reviewed / f"sft_chunk_{idx}_{shard}.approved.jsonl")
    pref_rows, bad_pref = safe_read_jsonl(reviewed / f"pref_chunk_{idx}_{shard}.approved.jsonl")
    if bad_sft or bad_pref:
        return [], []
    return sft_rows[:target_sft], pref_rows[:target_pref]


def write_tmp_merge(chunk_id: int, sft_rows: List[Dict[str, Any]], pref_rows: List[Dict[str, Any]]) -> Tuple[Path, Path]:
    idx = f"{chunk_id:04d}"
    chunk_dir = OUTPUT_ROOT / "chunks"
    tmp_sft = chunk_dir / f"sft_chunk_{idx}.tmp.jsonl"
    tmp_pref = chunk_dir / f"pref_chunk_{idx}.tmp.jsonl"
    write_jsonl(tmp_sft, sft_rows)
    write_jsonl(tmp_pref, pref_rows)
    return tmp_sft, tmp_pref


def commit_chunk_files(
    chunk_id: int,
    tmp_sft: Path,
    tmp_pref: Path,
    sft_target: int,
    pref_target: int,
    dedupe_signatures: set[str],
) -> Tuple[bool, str, set[str]]:
    idx = f"{chunk_id:04d}"
    chunk_dir = OUTPUT_ROOT / "chunks"
    final_sft = chunk_dir / f"sft_chunk_{idx}.jsonl"
    final_pref = chunk_dir / f"pref_chunk_{idx}.jsonl"

    sft_rows, bad_sft = safe_read_jsonl(tmp_sft)
    pref_rows, bad_pref = safe_read_jsonl(tmp_pref)
    if bad_sft or bad_pref:
        return False, "invalid_tmp_json", dedupe_signatures

    if len(sft_rows) < sft_target or len(pref_rows) < pref_target:
        return False, "insufficient_rows_after_trim", dedupe_signatures

    # dedupe check within and across chunks (global + local)
    local_signatures: set[str] = set()
    combined: List[str] = []
    selected_sft: List[Dict[str, Any]] = []
    selected_pref: List[Dict[str, Any]] = []

    for row in sft_rows:
        if len(selected_sft) >= sft_target:
            break
        try:
            prompt, assistant = extract_sft_signature(row)
            if not prompt or not assistant:
                return False, "invalid_row_schema", dedupe_signatures
        except Exception:
            return False, "invalid_row_schema", dedupe_signatures
        sig = f"sft:{exact_signature(prompt, assistant)}"
        if sig in dedupe_signatures or sig in local_signatures:
            continue
        local_signatures.add(sig)
        selected_sft.append(row)
        combined.append(sig)

    for row in pref_rows:
        if len(selected_pref) >= pref_target:
            break
        try:
            prompt, chosen = extract_pref_signature(row)
            if not prompt:
                prompt = row.get("messages_flat", {}).get("user", "")
            if not chosen:
                chosen = row.get("chosen", "")
            if not prompt or not chosen:
                return False, "invalid_row_schema", dedupe_signatures
        except Exception:
            return False, "invalid_row_schema", dedupe_signatures
        sig = f"pref:{signature_pref(prompt, chosen)}"
        if sig in dedupe_signatures or sig in local_signatures:
            continue
        local_signatures.add(sig)
        selected_pref.append(row)
        combined.append(sig)

    if len(selected_sft) < sft_target or len(selected_pref) < pref_target:
        return (
            False,
            f"insufficient_rows_after_global_dedupe:{len(selected_sft)}/{sft_target}:{len(selected_pref)}/{pref_target}",
            dedupe_signatures,
        )

    # Commit atomically.
    tmp_final_sft = final_sft.with_suffix(final_sft.suffix + ".commit.tmp")
    tmp_final_pref = final_pref.with_suffix(final_pref.suffix + ".commit.tmp")
    write_jsonl(tmp_final_sft, selected_sft)
    write_jsonl(tmp_final_pref, selected_pref)

    def safe_replace(source: Path, target: Path) -> bool:
        for _ in range(2):
            try:
                if target.exists():
                    try:
                        target.unlink()
                    except Exception:
                        pass
                os.replace(source, target)
                return True
            except PermissionError:
                # Windows often transiently locks files after subprocess writes.
                pass
        return False

    for target_path in [final_sft, final_pref]:
        if target_path.exists():
            try:
                target_path.unlink()
            except Exception:
                pass

    # Windows can intermittently lock files, so retry with best-effort cleanup.
    if not safe_replace(tmp_final_sft, final_sft):
        return False, f"commit_replace_failed:{final_sft.name}", dedupe_signatures
    if not safe_replace(tmp_final_pref, final_pref):
        return False, f"commit_replace_failed:{final_pref.name}", dedupe_signatures

    dedupe_signatures.update(combined)
    return True, "ok", combined


def merge_chunk_for_review(chunk_id: int, target_sft: int, target_pref: int, run_id: str) -> Tuple[bool, str, int, int]:
    idx = f"{chunk_id:04d}"
    reviewed = OUTPUT_ROOT / "chunks" / "reviewed"
    a_sft, a_pref = load_chunk_rows(chunk_id, "gen_a", target_sft, target_pref)
    b_sft, b_pref = load_chunk_rows(chunk_id, "gen_b", target_sft, target_pref)

    if not a_sft and not b_sft:
        return False, "empty_shards", 0, 0

    merged_sft = a_sft + b_sft
    merged_pref = a_pref + b_pref

    if len(merged_sft) < target_sft or len(merged_pref) < target_pref:
        return False, "insufficient_merged_rows", len(merged_sft), len(merged_pref)

    deduped_sft: List[Dict[str, Any]] = []
    deduped_pref: List[Dict[str, Any]] = []
    seen_sft: set[str] = set()
    seen_pref: set[str] = set()

    for row in merged_sft:
        prompt, assistant = extract_sft_signature(row)
        sig = f"sft:{signature_pref(prompt, assistant)}"
        if sig in seen_sft:
            continue
        seen_sft.add(sig)
        deduped_sft.append(row)

    for row in merged_pref:
        prompt, chosen = extract_pref_signature(row)
        sig = f"pref:{signature_pref(prompt, chosen)}"
        if sig in seen_pref:
            continue
        seen_pref.add(sig)
        deduped_pref.append(row)

    if len(deduped_sft) < target_sft or len(deduped_pref) < target_pref:
        return (
            False,
            f"insufficient_unique_rows:{len(deduped_sft)}/{len(deduped_pref)}<"
            f"{target_sft}/{target_pref}",
            len(deduped_sft),
            len(deduped_pref),
        )

    # Keep all deduplicated rows so final commit can filter global collisions
    # before taking the exact target chunk size.
    merged_sft = deduped_sft
    merged_pref = deduped_pref

    tmp_sft, tmp_pref = write_tmp_merge(chunk_id, merged_sft, merged_pref)

    ok, msg = run_reviewer(
        {
            "run_id": run_id,
            "chunk_id": chunk_id,
            "target": "merge",
            "target_sft_shard": target_sft,
            "target_pref_shard": target_pref,
        }
    )
    if not ok:
        return False, f"review_merge_failed:{msg}", 0, 0

    return True, "ok", len(merged_sft), len(merged_pref)


def run_review_for_target(run_id: str, chunk_id: int, target: str, output_root: Path) -> Tuple[bool, str]:
    cmd = [
        str(WORKER_PATH),
        "--mode",
        "reviewer",
        "--config",
        str(CONFIG_PATH),
        "--run-id",
        run_id,
        "--chunk-id",
        str(chunk_id),
        "--review-target",
        target,
        "--target-sft-shard",
        str(0),
        "--target-pref-shard",
        str(0),
        "--output-root",
        str(output_root),
    ]
    proc = call_worker(cmd)
    return proc.returncode == 0, (proc.stdout or "") + (proc.stderr or "")


def sorted_chunk_paths(prefix: str) -> List[Path]:
    chunk_dir = OUTPUT_ROOT / "chunks"
    files = sorted(chunk_dir.glob(f"{prefix}_*.jsonl"))
    return files


def validate_and_read_chunks(sft: bool, target_expected: int) -> Tuple[List[Dict[str, Any]], bool, str]:
    pattern = r"^sft_chunk_\d{4}\.jsonl$" if sft else r"^pref_chunk_\d{4}\.jsonl$"
    chunk_dir = OUTPUT_ROOT / "chunks"
    files = [
        p
        for p in sorted(chunk_dir.glob("*.jsonl"))
        if re.match(pattern, p.name)
    ]

    all_rows: List[Dict[str, Any]] = []
    for file in files:
        rows, bad = safe_read_jsonl(file)
        if bad:
            return [], False, f"invalid_json:{file.name}"
        all_rows.extend(rows)
    return all_rows, True, ""


def write_final_artifacts(
    state: Dict[str, Any],
    sft_rows: List[Dict[str, Any]],
    pref_rows: List[Dict[str, Any]],
    config: Dict[str, Any],
    run_id: str,
    seed: int = 3407,
) -> None:
    builder = IdentityDatasetBuilder(config, random.Random(seed), run_id, OUTPUT_ROOT)
    builder.target_sft = state["target_sft"]
    builder.target_pairs = state["target_pref"]

    category = builder.category_manifest(sft_rows)
    language = builder.language_manifest(sft_rows)
    multimodal = builder.multimodal_manifest(sft_rows)
    review = {
        "run_id": run_id,
        "generated_at_utc": now_utc(),
        "status": "completed",
        "counts": {
            "sft_rows_generated": len(sft_rows),
            "preference_pairs_generated": len(pref_rows),
            "candidate_count": 0,
        },
        "sft_target": state["target_sft"],
        "pair_target": state["target_pref"],
        "within_targets": True,
        "category_manifest": category,
        "language_manifest": language,
        "multimodal_manifest": multimodal,
        "filter_stats": {
            "source": "chunked_supervisor",
        },
        "quality_warnings": [
            "Deterministic deterministic chunks with local worker validation."
        ],
    }

    write_jsonl(OUTPUT_ROOT / "sft_dataset.jsonl", sft_rows)
    write_jsonl(OUTPUT_ROOT / "preference_dataset.jsonl", pref_rows)
    atomic_write_json(OUTPUT_ROOT / "category_manifest.json", category)
    atomic_write_json(OUTPUT_ROOT / "language_manifest.json", language)
    atomic_write_json(OUTPUT_ROOT / "multimodal_manifest.json", multimodal)
    atomic_write_json(OUTPUT_ROOT / "review_report.json", review)

    spot_checks = builder.spot_checks(sft_rows, count=config["validation"].get("spot_check_count", 25))
    stress_pack = builder.stress_tests(sft_rows)
    write_jsonl(OUTPUT_ROOT / "spot_checks.jsonl", spot_checks)
    write_jsonl(OUTPUT_ROOT / "stress_test_pack.jsonl", stress_pack)

    run_manifest = {
        "run_id": run_id,
        "generated_at_utc": now_utc(),
        "target_sft": state["target_sft"],
        "target_pref": state["target_pref"],
        "sft_rows": len(sft_rows),
        "preference_pairs": len(pref_rows),
        "status": "completed",
    }
    atomic_write_json(OUTPUT_ROOT / "run_manifest.json", run_manifest)

    # direct policy copy
    OUTPUT_ROOT.joinpath("identity_policy_sheet.md").write_text(
        POLICY_PATH.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    how_path = OUTPUT_ROOT / "how_dataset_could_still_fail.md"
    how_path.write_text(
        "# How this dataset could still fail\n\n"
        "- Near-duplicate threshold control is per-shard and can miss cross-window paraphrases.\n"
        "- Identity edge cases in low-frequency languages are less represented in generated samples.\n"
        "- Visual-policy consistency is not verified with real image artifacts in this mode.\n",
        encoding="utf-8",
    )


def run_finalization(state: Dict[str, Any]) -> bool:
    config = load_or_prepare_config(CONFIG_PATH)

    sft_rows, sft_ok, sft_err = validate_and_read_chunks(True, state["target_sft"])
    if not sft_ok:
        print(f"FINALIZE_BLOCKED reason=invalid_json")
        return False

    pref_rows, pref_ok, pref_err = validate_and_read_chunks(False, state["target_pref"])
    if not pref_ok:
        print(f"FINALIZE_BLOCKED reason=invalid_json")
        return False

    if len(sft_rows) < state["target_sft"] or len(pref_rows) < state["target_pref"]:
        print("FINALIZE_BLOCKED reason=target_shortfall")
        return False

    # trim to exact targets
    sft_rows = sft_rows[: state["target_sft"]]
    pref_rows = pref_rows[: state["target_pref"]]

    write_final_artifacts(state, sft_rows, pref_rows, config, state["run_id"], seed=config["validation"].get("random_seed", 3407))

    # mandatory final reviews
    for target in ["final_sft", "final_pref", "final_report"]:
        ok, out = run_review_for_target(state["run_id"], state["next_chunk"], target, OUTPUT_ROOT)
        if not ok:
            print("FINALIZE_BLOCKED reason=review_failed")
            return False

    return True


def chunk_loop() -> None:
    config = load_or_prepare_config(CONFIG_PATH)
    state_path = OUTPUT_ROOT / "state.json"
    state = bootstrap_state(config)
    write_state = lambda: atomic_write_json(state_path, state)

    gen_total = 0
    review_total = 0

    while True:
        append_heartbeat(state)

        if state.get("status") not in {"active", "finalized", "fatal"}:
            return

        if state.get("status") == "finalized":
            return

        if (
            state.get("sft_written", 0) >= state["target_sft"]
            and state.get("pref_written", 0) >= state["target_pref"]
        ):
            if run_finalization(state):
                state["status"] = "finalized"
                state["updated_at_utc"] = now_utc()
                write_state()
                print(f"FINALIZE_COMPLETE run_id={state['run_id']}")
                print(f"gen_subagents_total={gen_total}")
                print(f"review_subagents_total={review_total}")
                print(f"sft_rows={state['target_sft']}")
                print(f"preference_pairs={state['target_pref']}")
                print(f"output={OUTPUT_ROOT.as_posix()}")
                return
            state["status"] = "fatal"
            state["updated_at_utc"] = now_utc()
            write_state()
            print(f"FATAL_ABORT run_id={state['run_id']}")
            print(f"chunk_id={state['next_chunk']}")
            print(f"reason=review_failed")
            print(f"state_file={state_path.as_posix()}")
            return

        remaining_sft = max(0, state["target_sft"] - state["sft_written"])
        remaining_pref = max(0, state["target_pref"] - state["pref_written"])

        chunk_sft = min(state["chunk_sft"], remaining_sft)
        chunk_pref = min(state["chunk_pref"], remaining_pref)

        if chunk_sft == 0 and chunk_pref == 0:
            # guard rail in case of inconsistent accounting
            state["status"] = "finalized"
            continue

        chunk_id = int(state["next_chunk"])
        retry_attempts = 3
        chunk_failed = True
        retry_sft = chunk_sft
        retry_pref = chunk_pref
        dedupe_set = read_dedupe_set()
        failure_reasons: List[str] = []

        for attempt in range(retry_attempts):
            if attempt == 2:
                retry_sft = max(state["chunk_sft_min"], max(1, math.floor(retry_sft / 2)))
                retry_pref = max(state["chunk_pref_min"], max(1, math.floor(retry_pref / 2)))

            try:
                seed_base = int(
                    hashlib.sha256(f"{state['run_id']}:{chunk_id}:{attempt}".encode("utf-8")).hexdigest()[:8],
                    16,
                )
            except Exception:
                seed_base = attempt * 1000

            # validate pending files first
            need_generate = True
            if pending_rows_valid(chunk_id, "gen_a", retry_sft, retry_pref, state["run_id"]) and pending_rows_valid(
                chunk_id, "gen_b", retry_sft, retry_pref, state["run_id"]
            ):
                need_generate = False

            if not need_generate:
                if not (
                    (OUTPUT_ROOT / "chunks" / "pending" / f"meta_chunk_{chunk_id:04d}_gen_a.json").exists()
                    and (OUTPUT_ROOT / "chunks" / "pending" / f"meta_chunk_{chunk_id:04d}_gen_b.json").exists()
                ):
                    need_generate = True

            if need_generate:
                cleanup_chunk(chunk_id)
                with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
                    fa = ex.submit(run_generator, state["run_id"], chunk_id, "gen_a", retry_sft, retry_pref, seed_base + 11)
                    fb = ex.submit(run_generator, state["run_id"], chunk_id, "gen_b", retry_sft, retry_pref, seed_base + 22)
                    oka, _ = fa.result()
                    okb, _ = fb.result()
                gen_total += 2
                if not (oka and okb):
                    failure_reasons.append("generation_failed")
                    state["consecutive_failures"] += 1
                    continue

            # review shards
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
                ra = ex.submit(
                    run_reviewer,
                    {
                        "run_id": state["run_id"],
                        "chunk_id": chunk_id,
                        "target": "gen_a",
                        "target_sft_shard": retry_sft,
                        "target_pref_shard": retry_pref,
                    },
                )
                rb = ex.submit(
                    run_reviewer,
                    {
                        "run_id": state["run_id"],
                        "chunk_id": chunk_id,
                        "target": "gen_b",
                        "target_sft_shard": retry_sft,
                        "target_pref_shard": retry_pref,
                    },
                )
                oka, loga = ra.result()
                okb, logb = rb.result()
            review_total += 2
            if not (oka and okb):
                failure_reasons.append(f"review_shards_failed:{loga}|{logb}")
                cleanup_chunk(chunk_id)
                state["consecutive_failures"] += 1
                continue

            ok, merge_msg, merged_sft_count, merged_pref_count = merge_chunk_for_review(
                chunk_id,
                retry_sft,
                retry_pref,
                state["run_id"],
            )
            if not ok:
                failure_reasons.append(f"merge_prepare:{merge_msg}")
                state["consecutive_failures"] += 1
                cleanup_chunk(chunk_id)
                continue

            tmp_sft = OUTPUT_ROOT / "chunks" / f"sft_chunk_{chunk_id:04d}.tmp.jsonl"
            tmp_pref = OUTPUT_ROOT / "chunks" / f"pref_chunk_{chunk_id:04d}.tmp.jsonl"
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                rr = ex.submit(
                    run_reviewer,
                    {
                        "run_id": state["run_id"],
                        "chunk_id": chunk_id,
                        "target": "merge",
                        "target_sft_shard": retry_sft,
                        "target_pref_shard": retry_pref,
                    },
                )
                okm, review_merge_msg = rr.result()
            review_total += 1
            if not okm:
                failure_reasons.append(f"review_merge_failed:{review_merge_msg}")
                state["consecutive_failures"] += 1
                cleanup_chunk(chunk_id)
                continue

            merged_sft_rows, _ = safe_read_jsonl(tmp_sft)
            merged_pref_rows, _ = safe_read_jsonl(tmp_pref)
            merged_sft_rows = merged_sft_rows[:retry_sft]
            merged_pref_rows = merged_pref_rows[:retry_pref]

            # commit with dedupe guard
            tmp_signatures = set()
            _, commit_msg, tmp_signatures = commit_chunk_files(
                chunk_id,
                tmp_sft,
                tmp_pref,
                retry_sft,
                retry_pref,
                dedupe_set,
            )
            if commit_msg == "exact_dedupe_hit":
                failure_reasons.append("exact_dedupe_hit")
                state["consecutive_failures"] += 1
                cleanup_chunk(chunk_id)
                continue
            if commit_msg != "ok":
                failure_reasons.append(f"commit_failed:{commit_msg}")
                cleanup_chunk(chunk_id)
                state["consecutive_failures"] += 1
                continue

            append_dedupe_signatures(tmp_signatures)
            dedupe_set = read_dedupe_set()

            # commit success
            state["sft_written"] += retry_sft
            state["pref_written"] += retry_pref
            state["next_chunk"] += 1
            state["consecutive_failures"] = 0
            state["updated_at_utc"] = now_utc()
            write_state()
            chunk_failed = False
            break

        if chunk_failed:
            state["status"] = "fatal"
            state["updated_at_utc"] = now_utc()
            write_state()
            fatal_path = OUTPUT_ROOT / f"fatal_chunk_{chunk_id:04d}.json"
            atomic_write_json(
                fatal_path,
                {
                    "run_id": state["run_id"],
                    "chunk_id": chunk_id,
                    "reasons": failure_reasons,
                    "attempts": retry_attempts,
                    "updated_at_utc": now_utc(),
                },
            )
            print(f"FATAL_ABORT run_id={state['run_id']}")
            print(f"chunk_id={chunk_id}")
            print(f"reason=fatal_after_retries")
            print(f"state_file={state_path.as_posix()}")
            return


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run Codex Spark xhigh autonomous generation")
    p.add_argument("--run-id", default=None, help="Optional run id override")
    p.add_argument("--seed", type=int, default=3407)
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    # Required input reads before any writes.
    config = load_or_prepare_config(CONFIG_PATH)
    for path in [CONFIG_PATH, POLICY_PATH, MANUAL_WRITER_PATH, Path(__file__).with_name("identity_dataset_builder.py")]:
        if not path.exists():
            print(f"Required input missing: {path}")
            return 1

    # Bootstrap and then run until completion.
    if args.run_id:
        # keep explicit override
        state = bootstrap_state(config)
        state["run_id"] = args.run_id
        atomic_write_json(OUTPUT_ROOT / "state.json", state)
    else:
        state = bootstrap_state(config)

    if args.dry_run:
        print("DRY_RUN_OK")
        return 0

    chunk_loop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
