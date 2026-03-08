"""Standalone helpers embedded into the unified Colab notebook.

These helpers are written in normal Python so they can be unit-tested in the
repo, then embedded into notebook 90 as runtime source text. The notebook
itself should not rely on repo-side imports at execution time.
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
import textwrap
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw


PLACEHOLDER_PREFIXES = ("image://", "synthetic://")
TEXT_ONLY_SOURCES = {
    "HuggingFaceH4/ultrachat_200k",
    "CohereLabs/aya_dataset",
    "allenai/WildChat-4.8M",
    "HuggingFaceTB/smoltalk2",
    "nvidia/HelpSteer3",
    "argilla/ultrafeedback-binarized-preferences-cleaned",
}
MULTIMODAL_SOURCES = {
    "HuggingFaceM4/Docmatix",
    "facebook/textvqa",
    "lmms-lab/DocVQA",
    "HuggingFaceM4/the_cauldron",
}


def sha256_file(path: str | Path) -> str:
    handle_path = Path(path)
    digest = hashlib.sha256()
    with handle_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_text(value: Any) -> str:
    if isinstance(value, str):
        return " ".join(value.replace("\u00a0", " ").split()).strip()
    if isinstance(value, list):
        parts = [normalize_text(item) for item in value]
        return " ".join(part for part in parts if part).strip()
    if isinstance(value, dict):
        if isinstance(value.get("text"), str):
            return normalize_text(value["text"])
        if isinstance(value.get("content"), str):
            return normalize_text(value["content"])
    return ""


def best_effort_user_text(messages: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for message in messages:
        if not isinstance(message, dict) or message.get("role") != "user":
            continue
        content = message.get("content")
        if isinstance(content, str):
            text = normalize_text(content)
            if text:
                parts.append(text)
            continue
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text = normalize_text(block.get("text"))
                    if text:
                        parts.append(text)
    return "\n".join(parts).strip()


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def create_surrogate_document_image(prompt_text: str, destination: str | Path) -> Path:
    """Create a deterministic document/screenshot-like image for placeholder rows."""
    dest = Path(destination).expanduser().resolve()
    _ensure_parent(dest)
    image = Image.new("RGB", (1344, 1024), (248, 248, 245))
    draw = ImageDraw.Draw(image)
    draw.rectangle((48, 48, 1296, 976), outline=(188, 188, 188), width=3)
    draw.rectangle((84, 84, 1260, 160), fill=(225, 229, 235))
    draw.text((108, 112), "Lumis-1 surrogate document context", fill=(32, 32, 32))
    wrapped = textwrap.wrap(prompt_text or "Image context placeholder", width=58)[:22]
    y = 210
    for line in wrapped:
        draw.text((108, y), line, fill=(24, 24, 24))
        y += 34
    draw.text((108, 922), "Generated from placeholder image reference", fill=(90, 90, 90))
    image.save(dest, format="PNG")
    return dest


def materialize_image_value(image_value: Any, destination: str | Path) -> Path:
    """Persist one image-like value to a local PNG/JPEG path."""
    dest = Path(destination).expanduser().resolve()
    _ensure_parent(dest)

    if isinstance(image_value, Image.Image):
        image_value.save(dest)
        return dest

    if isinstance(image_value, dict):
        if isinstance(image_value.get("bytes"), (bytes, bytearray)):
            Image.open(io.BytesIO(image_value["bytes"])).save(dest)
            return dest
        if isinstance(image_value.get("bytes"), str) and image_value["bytes"].strip():
            raw = base64.b64decode(image_value["bytes"])
            Image.open(io.BytesIO(raw)).save(dest)
            return dest
        if isinstance(image_value.get("path"), str) and image_value["path"].strip():
            return materialize_image_value(image_value["path"], dest)
        if isinstance(image_value.get("url"), str) and image_value["url"].strip():
            return materialize_image_value(image_value["url"], dest)

    if isinstance(image_value, (bytes, bytearray)):
        Image.open(io.BytesIO(image_value)).save(dest)
        return dest

    if isinstance(image_value, str) and image_value.strip():
        value = image_value.strip()
        lowered = value.lower()
        if lowered.startswith(("http://", "https://")):
            with urllib.request.urlopen(value) as response:
                raw = response.read()
            Image.open(io.BytesIO(raw)).save(dest)
            return dest
        path = Path(value).expanduser()
        if path.exists():
            image = Image.open(path)
            image.save(dest)
            return dest

    raise ValueError(f"unsupported image value for materialization: {type(image_value)!r}")


def make_image_block(path: str | Path) -> dict[str, str]:
    resolved = str(Path(path).expanduser().resolve())
    return {
        "type": "image",
        "image": resolved,
        "path": resolved,
        "image_path": resolved,
    }


def normalize_messages_as_blocks(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        role = str(message.get("role") or "user")
        content = message.get("content")
        if isinstance(content, str):
            normalized.append({"role": role, "content": [{"type": "text", "text": content}]})
            continue
        if isinstance(content, list):
            blocks: list[dict[str, Any]] = []
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "text":
                    text = normalize_text(block.get("text"))
                    if text:
                        blocks.append({"type": "text", "text": text})
                elif block.get("type") == "image":
                    image_block = {"type": "image"}
                    for key in ("image", "path", "image_path", "image_bytes_b64"):
                        if isinstance(block.get(key), str) and str(block[key]).strip():
                            image_block[key] = str(block[key]).strip()
                    blocks.append(image_block)
            if blocks:
                normalized.append({"role": role, "content": blocks})
    return normalized


def materialize_identity_placeholder_assets(
    rows: list[dict[str, Any]],
    asset_root: str | Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    asset_dir = Path(asset_root).expanduser().resolve()
    asset_dir.mkdir(parents=True, exist_ok=True)
    materialized: list[dict[str, Any]] = []
    placeholder_rows = 0
    created_images = 0

    for row in rows:
        current = json.loads(json.dumps(row))
        current["messages"] = normalize_messages_as_blocks(list(current.get("messages") or []))
        prompt_text = best_effort_user_text(current["messages"])
        for message in current["messages"]:
            content = message.get("content")
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict) or block.get("type") != "image":
                    continue
                image_ref = block.get("image")
                if isinstance(image_ref, str) and image_ref.startswith(PLACEHOLDER_PREFIXES):
                    placeholder_rows += 1
                    stem = hashlib.sha256(f"{current.get('id')}::{image_ref}".encode("utf-8")).hexdigest()[:20]
                    asset_path = asset_dir / f"{stem}.png"
                    if not asset_path.exists():
                        create_surrogate_document_image(prompt_text, asset_path)
                        created_images += 1
                    block.update(make_image_block(asset_path))
        current["modality"] = "image_text" if "image_path" in json.dumps(current, ensure_ascii=False) else "text"
        materialized.append(current)

    report = {
        "rows_input": len(rows),
        "rows_output": len(materialized),
        "placeholder_blocks_seen": placeholder_rows,
        "surrogate_images_created": created_images,
        "asset_root": str(asset_dir),
    }
    return materialized, report


def _pick_first_text(*candidates: Any) -> str:
    for candidate in candidates:
        text = normalize_text(candidate)
        if text:
            return text
    return ""


def _pick_majority_answer(values: Any) -> str:
    if isinstance(values, str):
        return normalize_text(values)
    if isinstance(values, list):
        normalized = [normalize_text(item) for item in values if normalize_text(item)]
        if not normalized:
            return ""
        return Counter(normalized).most_common(1)[0][0]
    return ""


def _save_named_image(source_id: str, row_id: str, image_value: Any, asset_root: Path) -> Path:
    stem = hashlib.sha256(f"{source_id}::{row_id}".encode("utf-8")).hexdigest()[:20]
    destination = asset_root / source_id.replace("/", "__") / f"{stem}.png"
    if destination.exists():
        return destination
    return materialize_image_value(image_value, destination)


def build_multimodal_row_from_record(
    source_id: str,
    record: dict[str, Any],
    *,
    asset_root: str | Path,
    row_id: str,
) -> dict[str, Any] | None:
    asset_dir = Path(asset_root).expanduser().resolve()
    asset_dir.mkdir(parents=True, exist_ok=True)

    if source_id == "facebook/textvqa":
        question = _pick_first_text(record.get("question"))
        answer = _pick_majority_answer(record.get("answers"))
        image_value = record.get("image")
        if question and answer and image_value is not None:
            image_path = _save_named_image(source_id, row_id, image_value, asset_dir)
            return {
                "id": row_id,
                "source_id": source_id,
                "license": "CC-BY-4.0",
                "thinking": "off",
                "chat_template_kwargs": {"enable_thinking": False},
                "category": "utility_tasks",
                "modality": "image_text",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            make_image_block(image_path),
                            {"type": "text", "text": question},
                        ],
                    },
                    {"role": "assistant", "content": [{"type": "text", "text": answer}]},
                ],
            }

    if source_id == "lmms-lab/DocVQA":
        query = record.get("query")
        question = _pick_first_text(
            record.get("question"),
            query.get("en") if isinstance(query, dict) else query,
            query.get("question") if isinstance(query, dict) else None,
        )
        answer = _pick_majority_answer(record.get("answers") or record.get("answer"))
        image_value = record.get("image") or record.get("page_image")
        if question and answer and image_value is not None:
            image_path = _save_named_image(source_id, row_id, image_value, asset_dir)
            return {
                "id": row_id,
                "source_id": source_id,
                "license": "Apache-2.0",
                "thinking": "off",
                "chat_template_kwargs": {"enable_thinking": False},
                "category": "utility_tasks",
                "modality": "image_text",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            make_image_block(image_path),
                            {"type": "text", "text": question},
                        ],
                    },
                    {"role": "assistant", "content": [{"type": "text", "text": answer}]},
                ],
            }

    if source_id == "HuggingFaceM4/Docmatix":
        image_value = record.get("image")
        if image_value is None and isinstance(record.get("images"), list) and record["images"]:
            image_value = record["images"][0]
        qa_pairs = record.get("texts")
        if isinstance(qa_pairs, list):
            for index, pair in enumerate(qa_pairs):
                if not isinstance(pair, dict):
                    continue
                question = _pick_first_text(pair.get("user"), pair.get("question"), pair.get("prompt"))
                answer = _pick_first_text(pair.get("assistant"), pair.get("answer"), pair.get("response"))
                if question and answer and image_value is not None:
                    image_path = _save_named_image(source_id, f"{row_id}-{index}", image_value, asset_dir)
                    return {
                        "id": f"{row_id}-{index}",
                        "source_id": source_id,
                        "license": "MIT",
                        "thinking": "off",
                        "chat_template_kwargs": {"enable_thinking": False},
                        "category": "utility_tasks",
                        "modality": "image_text",
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    make_image_block(image_path),
                                    {"type": "text", "text": question},
                                ],
                            },
                            {"role": "assistant", "content": [{"type": "text", "text": answer}]},
                        ],
                    }

    return None


def render_prompt_messages_to_text(prompt_messages: Any) -> str:
    if not isinstance(prompt_messages, list):
        return ""
    parts: list[str] = []
    for message in prompt_messages:
        if not isinstance(message, dict) or message.get("role") != "user":
            continue
        content = message.get("content")
        if isinstance(content, str):
            text = normalize_text(content)
            if text:
                parts.append(text)
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text = normalize_text(block.get("text"))
                    if text:
                        parts.append(text)
    return " ".join(parts).strip()


def normalize_messages_for_storage(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize chat rows into block form for notebook runtime storage."""
    normalized = normalize_messages_as_blocks(messages)
    compact: list[dict[str, Any]] = []
    for message in normalized:
        role = message["role"]
        blocks = message["content"]
        if role == "assistant":
            compact.append({"role": role, "content": blocks})
        else:
            compact.append({"role": role, "content": blocks})
    return compact


def build_text_row_from_record(
    source_id: str,
    record: dict[str, Any],
    *,
    row_id: str,
    license_name: str,
    category: str,
) -> dict[str, Any] | None:
    messages = record.get("messages")
    if isinstance(messages, list) and messages:
        normalized = normalize_messages_for_storage(messages)
    else:
        prompt = _pick_first_text(
            record.get("prompt"),
            record.get("instruction"),
            record.get("question"),
            record.get("input"),
        )
        answer = _pick_first_text(
            record.get("response"),
            record.get("output"),
            record.get("answer"),
            record.get("chosen"),
        )
        if not prompt or not answer:
            return None
        normalized = [
            {"role": "user", "content": [{"type": "text", "text": prompt}]},
            {"role": "assistant", "content": [{"type": "text", "text": answer}]},
        ]
    return {
        "id": row_id,
        "source_id": source_id,
        "license": license_name,
        "thinking": "off",
        "chat_template_kwargs": {"enable_thinking": False},
        "category": category,
        "modality": "text",
        "messages": normalized,
    }


def extract_preference_triplet(record: dict[str, Any]) -> tuple[str, str, str] | None:
    prompt = _pick_first_text(
        record.get("prompt"),
        record.get("instruction"),
        record.get("question"),
        record.get("input"),
    )
    chosen = _pick_first_text(record.get("chosen"))
    rejected = _pick_first_text(record.get("rejected"))
    if prompt and chosen and rejected:
        return prompt, chosen, rejected

    a = _pick_first_text(record.get("response_a"), record.get("answer_a"), record.get("candidate_a"))
    b = _pick_first_text(record.get("response_b"), record.get("answer_b"), record.get("candidate_b"))
    winner = _pick_first_text(record.get("winner"), record.get("label"), record.get("preference")).upper()
    if prompt and a and b and winner:
        if winner in {"A", "LEFT", "1", "CHOICE_A"}:
            return prompt, a, b
        if winner in {"B", "RIGHT", "2", "CHOICE_B"}:
            return prompt, b, a
    return None


def approximate_row_text(row: dict[str, Any]) -> str:
    parts: list[str] = []
    for message in row.get("messages", []):
        if not isinstance(message, dict):
            continue
        content = message.get("content")
        if isinstance(content, str):
            text = normalize_text(content)
            if text:
                parts.append(text)
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text = normalize_text(block.get("text"))
                    if text:
                        parts.append(text)
                elif isinstance(block, dict) and block.get("type") == "image":
                    parts.append("[image]")
    return "\n".join(parts).strip()
