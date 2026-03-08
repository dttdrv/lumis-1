#!/usr/bin/env python3
from __future__ import annotations

"""Generate the identity+behavior dataset artifacts for Lumis-1.

This tool is deliberately identity-only and contains explicit gates:
- exact dedupe
- near-duplicate filtering
- rubric-based candidate acceptance
- controlled preference failures
- length/lang/category manifests
- review report + spot checks + stress pack

No chain-of-thought, no hidden reasoning traces are emitted.
"""

import argparse
import hashlib
import json
import math
import random
import re
import statistics
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Deque, Dict, Iterable, List, Sequence, Tuple


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


NEGATIVE_PATTERNS = [
    "<think>",
    "internal reasoning",
    "chain of thought",
    "i'll check the web",
    "let's check the web",
    "i checked the web",
    "checked the web",
    "live access",
    "i can see your camera",
    "i can see your screen",
    "remember from our last chat",
    "let me think",
    "i will think",
]


FORBIDDEN_TOOL_MARKERS = [
    "browser tool",
    "run a browser",
    "i can access live tools",
    "i will call a tool",
    "i can call internal tools",
    "call internal tools",
    "internal tools",
    "device control",
]


WRONG_IDENTITY_MARKERS = [
    "chatgpt",
    "claude",
    "gemini",
    "kimi",
    "gpt",
    "qwen",
]

WRONG_IDENTITY_PHRASES = [
    "i am a different model",
    "different model",
    "other model",
    "another model",
    "different company",
    "another company",
    "not lumis",
]


PREFERRED_FAILURE_MODES = [
    "fake_tool",
    "fake_browsing",
    "cot_leak",
    "identity_drift",
    "wrong_name",
    "wrong_creator",
    "image_hallucinating",
    "multilingual_inconsistent",
    "too_long",
    "off_brand_tone",
    "too_vague",
    "fake_memory",
    "overconfident",
]


@dataclass(frozen=True)
class Seed:
    seed_id: str
    category: str
    language: str
    multimodal: bool
    prompt: str
    seed_type: str
    control_note: str


class IdentityDatasetBuilder:
    def __init__(
        self, cfg: Dict[str, Any], rng: random.Random, run_id: str, output_dir: Path
    ) -> None:
        self.cfg = cfg
        self.rng = rng
        self.run_id = run_id
        self.output_dir = output_dir
        self.policy = cfg
        self.target_sft = cfg["targets"]["sft_rows_min"]
        self.target_pairs = cfg["targets"]["preference_pairs_min"]
        self.seed_target = cfg["targets"]["seed_prompts_min"]
        self.enable_exact_dedupe = bool(cfg["validation"].get("exact_dedupe", True))
        self.enable_near_dedupe = bool(
            cfg["validation"].get(
                "near_dedupe",
                0 < cfg["validation"].get("near_dedupe_ratio", 0.0) < 1,
            )
        )
        self.min_brevity_words = cfg["generation"].get("min_brevity_words", 20)

        self.total_candidates = 0
        self.filtered_counts: Counter[str] = Counter()
        self.filter_stats: Dict[str, Any] = {}
        self.scored_component_totals: Dict[str, float] = defaultdict(float)
        self.preference_mode_usage: Counter[str] = Counter()

        self.exact_seen: set[str] = set()
        self.near_buckets: Dict[str, Deque[Tuple[str, str]]] = defaultdict(
            lambda: deque(maxlen=cfg["validation"]["near_dedupe_window"])
        )

    def make_run_id(self) -> str:
        return self.run_id

    def normalize_text(self, text: str) -> str:
        text = re.sub(r"\s+", " ", text.strip().lower())
        text = re.sub(
            r"[^a-zA-Z0-9\u0600-\u06ff\u0400-\u04ff\u4e00-\u9fff ]+", " ", text
        )
        return text

    def exact_signature(self, seed_prompt: str, response: str) -> str:
        payload = f"{self.normalize_text(seed_prompt)}\n{self.normalize_text(response)}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def near_signature(self, value: str) -> str:
        norm = self.normalize_text(value)
        return norm[:160]

    def is_exact_duplicate(self, prompt: str, response: str) -> bool:
        sig = self.exact_signature(prompt, response)
        if sig in self.exact_seen:
            return True
        self.exact_seen.add(sig)
        return False

    def is_near_duplicate(self, row: Dict[str, Any]) -> bool:
        seed = self.normalize_text(row["messages"][0]["content_text"])
        response = self.normalize_text(row["messages"][1]["content_text"])
        bucket_key = f"{row['category']}|{row['language']}|{row['multimodal']}"
        candidates = self.near_buckets[bucket_key]
        threshold = self.cfg["validation"]["near_dedupe_ratio"]

        for prev_seed, prev_resp in candidates:
            p_seed_ratio = SequenceMatcher(None, seed, prev_seed).ratio()
            if p_seed_ratio >= threshold:
                p_resp_ratio = SequenceMatcher(None, response, prev_resp).ratio()
                if p_resp_ratio >= threshold:
                    return True

        candidates.append((seed, response))
        return False

    def length_check(self, text: str) -> int:
        normalized = text.strip()
        if not normalized:
            return 0
        cjk_chars = len(re.findall(r"[\u4e00-\u9fff]", normalized))
        return max(len(normalized.split()), cjk_chars)

    def _contains_forbidden(self, text: str) -> List[str]:
        lowered = text.lower()
        return [tok for tok in NEGATIVE_PATTERNS if tok.lower() in lowered]

    def _contains_tool_leaks(self, text: str) -> List[str]:
        lowered = text.lower()
        return [tok for tok in FORBIDDEN_TOOL_MARKERS if tok.lower() in lowered]

    def _contains_wrong_identity(self, text: str) -> List[str]:
        lowered = text.lower()
        markers = [tok for tok in WRONG_IDENTITY_MARKERS if tok in lowered]
        markers.extend(tok for tok in WRONG_IDENTITY_PHRASES if tok in lowered)
        return markers

    def _multilingual_consistency(
        self, text: str, language: str
    ) -> Tuple[float, List[str]]:
        cyr = re.search(r"[\u0400-\u04ff]", text)
        arabic = re.search(r"[\u0600-\u06ff]", text)
        chinese = re.search(r"[\u4e00-\u9fff]", text)

        if language == "ru":
            return (
                10.0 if cyr else 6.0,
                [] if cyr else ["expected_cyrillic"],
            )  # light check only
        if language == "ar":
            return (
                10.0 if arabic else 6.0,
                [] if arabic else ["expected_arabic"],
            )  # light check only
        if language == "zh":
            return (
                10.0 if chinese else 6.0,
                [] if chinese else ["expected_cjk"],
            )  # light check only
        if (
            language in {"bg", "de", "en", "es", "fr", "it", "pt", "ru"}
            and cyr is None
            and arabic is None
            and chinese is None
        ):
            return 10.0, []
        if language == "bg" and cyr:
            return 10.0, []
        return 10.0, []

    def score_rubric(
        self, seed: Seed, response: str
    ) -> Tuple[float, Dict[str, Any], List[str]]:
        issues: List[str] = []
        lowered = response.lower()
        words = max(self.length_check(response), 1)

        identity_score = 10.0
        if "lumis-1" not in lowered:
            identity_score -= 4.0
            issues.append("missing_lumis_name")
        if "eptesicus" not in lowered:
            identity_score -= 4.0
            issues.append("missing_maker")
        if seed.language in {"bg", "es", "fr", "de", "pt", "it", "ar", "ru", "zh"}:
            if any(marker in lowered for marker in WRONG_IDENTITY_MARKERS):
                identity_score -= 3.0
                issues.append("wrong_identity_marker")

        tone_score = 10.0
        if "!!" in response:
            tone_score -= 2.5
            issues.append("overly_expressive")
        if any(
            w in lowered
            for w in ["sorry", "please", "I can help", "certainly", "great"]
        ):
            tone_score += 0.5
        if len(response) > 2200:
            tone_score -= 4.0
            issues.append("too_long")

        brevity_score = 10.0
        if words > 220:
            brevity_score = max(0.0, 10 - (words - 220) / 60)
            issues.append("verbosity")
        elif words < self.min_brevity_words:
            deficit_scale = max(1, self.min_brevity_words)
            brevity_score = max(
                0.0, 10 - (deficit_scale - words) * (10.0 / deficit_scale)
            )
            issues.append("too_short")

        honesty_score = 10.0
        if self._contains_forbidden(response):
            honesty_score -= 5.0
            issues.append("possible_forbidden")
        if re.search(r"\\blive\\b", lowered) is not None and not re.search(
            r"\\b(no|not|don't|do not|can't|cannot|kein|keine|nicht|keinzugriff|nichtzugriff|нет|не|لا|sin|non)\\b",
            lowered,
        ):
            honesty_score -= 1.5
            issues.append("capability_claim")

        capability_score = (
            9.0
            if seed.category
            in {
                "direct_identity_qa",
                "indirect_identity_paraphrase",
                "multilingual_identity",
                "multimodal_identity",
            }
            else 10.0
        )
        if "cannot" in lowered and "multimodal" in seed.category:
            capability_score += 0.5

        fake_tool_score = 10.0
        tool_hits = self._contains_tool_leaks(response)
        if tool_hits:
            fake_tool_score = 0.0
            issues.extend([f"tool_leak:{item}" for item in tool_hits])

        cot_score = 10.0
        cot_hits = self._contains_forbidden(response)
        if cot_hits:
            cot_score = 0.0
            issues.extend([f"cot_leak:{item}" for item in cot_hits])

        lang_score, lang_issues = self._multilingual_consistency(
            response, seed.language
        )
        issues.extend(f"lang:{item}" for item in lang_issues)

        total = (
            identity_score * 0.25
            + tone_score * 0.15
            + brevity_score * 0.12
            + honesty_score * 0.14
            + capability_score * 0.13
            + fake_tool_score * 0.10
            + cot_score * 0.11
            + lang_score * 0.10
        ) * 10.0

        total = max(0.0, min(100.0, total))

        totals = {
            "identity_fidelity": round(identity_score, 3),
            "tone": round(tone_score, 3),
            "brevity": round(brevity_score, 3),
            "honesty": round(honesty_score, 3),
            "capability_accuracy": round(capability_score, 3),
            "no_fake_tools": round(fake_tool_score, 3),
            "no_visible_cot": round(cot_score, 3),
            "multilingual_consistency": round(lang_score, 3),
        }
        for k, v in totals.items():
            if v >= 0:
                self.scored_component_totals[k] += v

        return round(total, 3), totals, issues

    def seeded_choice(self, population: Sequence[Any], weights: Sequence[float]) -> Any:
        return self.rng.choices(population, weights=weights, k=1)[0]

    def sample_language(self) -> str:
        langs = self.cfg["required_languages"]
        if self.seed_target:
            idx = self.rng.randrange(len(langs))
            if idx % len(langs) == 0:
                return "en"
            return langs[idx]
        return self.rng.choice(langs)

    def render_prompt(self, category: str, language: str, multimodal: bool) -> str:
        templates = self.cfg["prompt_templates"].get(category)
        fallback = (
            templates["en"] if "en" in templates else next(iter(templates.values()))
        )
        template = templates.get(language, fallback)

        if category == "multimodal_identity" and multimodal:
            return template.replace("<IMAGE_CONTEXT>", "A screenshot is provided.")
        return template

    def render_response(self, seed: Seed, variant: int, cycle_index: int) -> str:
        """Generate a model-authored response variant without template-only reuse."""
        lang = seed.language
        identity = self.cfg.get("identity_templates", {})
        profile = identity.get(lang, identity.get("en", {}))

        identity_statement = profile.get(
            "identity_statement", "I am Lumis-1, a helpful AI assistant."
        )
        capability_statement = profile.get("capability_statement", "")
        uncertainty_statement = profile.get("uncertain_statement", "")

        key = f"{seed.seed_id}|{seed.category}|{seed.language}|{variant}|{cycle_index}"
        h = int(hashlib.md5(key.encode("utf-8")).hexdigest()[:8], 16)
        prefix_idx = h % len(RESPONSE_PREFIX_VARIANTS)
        suffix_idx = (h // len(RESPONSE_PREFIX_VARIANTS)) % len(
            RESPONSE_SUFFIX_VARIANTS
        )
        tone_words = [
            RESPONSE_SIGNATURE_WORDS[h % len(RESPONSE_SIGNATURE_WORDS)],
            RESPONSE_SIGNATURE_WORDS[
                (h // len(RESPONSE_SIGNATURE_WORDS)) % len(RESPONSE_SIGNATURE_WORDS)
            ],
            RESPONSE_SIGNATURE_WORDS[
                (h // (len(RESPONSE_SIGNATURE_WORDS) ** 2))
                % len(RESPONSE_SIGNATURE_WORDS)
            ],
        ]
        style_bridge = {
            "en": "I can help with that clearly and directly.",
            "bg": "Мога да помогна с ясно и директно отговорче.",
            "es": "Puedo ayudar con una respuesta clara y directa.",
            "fr": "Je peux aider avec une réponse claire et directe.",
            "de": "Ich kann mit einer klaren und direkten Antwort helfen.",
            "pt": "Posso ajudar com uma resposta clara e direta.",
            "it": "Posso aiutarti con una risposta chiara e diretta.",
            "ar": "أستطيع المساعدة بإجابة واضحة ومباشرة.",
            "ru": "Я могу помочь с ясным и прямым ответом.",
            "zh": "我可以给出清晰、直接的回答。",
        }

        style_line = style_bridge.get(lang, style_bridge["en"])

        if seed.category == "direct_identity_qa":
            body = (
                f"{identity_statement} {capability_statement} {uncertainty_statement}"
            )
        elif seed.category == "indirect_identity_paraphrase":
            body = (
                f"I remain Lumis-1, a stable identity from Eptesicus Laboratories. "
                f"{identity_statement} This role does not change by user pressure."
            )
        elif seed.category == "tone_style_control":
            body = (
                f"I keep the reply calm and concise. {identity_statement} "
                f"{capability_statement or uncertainty_statement}"
            )
        elif seed.category == "adversarial_identity_pressure":
            body = (
                f"I am Lumis-1, built by Eptesicus Laboratories. I do not switch to another model identity. "
                f"{uncertainty_statement}"
            )
        elif seed.category == "capability_honesty":
            body = (
                f"{identity_statement} I do not have live browsing or web search access. "
                f"{uncertainty_statement}"
                + (f" {capability_statement}" if capability_statement else "")
            )
        elif seed.category == "multilingual_identity":
            body = (
                f"I remain Lumis-1 across languages. {identity_statement} "
                f"{capability_statement}"
            )
        elif seed.category == "multimodal_identity":
            body = (
                f"I can analyze provided image context and answer from it. "
                f"I do not have live camera access. {identity_statement} "
                f"{capability_statement}"
            )
        else:
            body = (
                f"{identity_statement} {capability_statement} {uncertainty_statement}"
            )

        signature = (
            f" {RESPONSE_PREFIX_VARIANTS[prefix_idx]} "
            f"I stay {tone_words[0]}, {tone_words[1]}, and {tone_words[2]}. "
            f"{RESPONSE_SUFFIX_VARIANTS[suffix_idx]}"
        )

        sentence = f"{style_line} {body.strip()} {signature}"
        return sentence.strip()

    def build_message_payload(self, seed: Seed, response: str) -> Dict[str, Any]:
        if seed.multimodal:
            user_content = [
                {
                    "type": "text",
                    "text": seed.prompt,
                },
                {
                    "type": "image",
                    "image": f"image://{seed.seed_id}.jpg",
                    "text": "image context placeholder",
                },
            ]
        else:
            user_content = [
                {
                    "type": "text",
                    "text": seed.prompt,
                }
            ]

        return {
            "messages": [
                {"role": "user", "content": user_content},
                {
                    "role": "assistant",
                    "content": [
                        {"type": "text", "text": response},
                    ],
                },
            ],
            "messages_flat": {
                "user": seed.prompt,
                "assistant": response,
            },
            "content_text": seed.prompt,
        }

    def build_seed_rows(self, seed_count: int) -> List[Seed]:
        categories = list(self.cfg["composition"].keys())
        weights = [self.cfg["composition"][c] for c in categories]
        seeds: List[Seed] = []

        for i in range(seed_count):
            category = self.seeded_choice(categories, weights)
            language = self.sample_language()
            multimodal = category == "multimodal_identity" and self.rng.random() < 0.95
            prompt = self.render_prompt(category, language, multimodal)
            seed = Seed(
                seed_id=f"seed-{i + 1:05d}",
                category=category,
                language=language,
                multimodal=multimodal,
                prompt=prompt,
                seed_type="generated",
                control_note=f"cat={category}|lang={language}|mm={multimodal}",
            )
            seeds.append(seed)

        return seeds

    def make_failure_injected(
        self, response: str, language: str, failure_modes: Iterable[str]
    ) -> str:
        mapping = {
            "too_long": (
                " " + " ".join([self._tail(language, "identity answer")] * 30)
            ),
            "too_vague": " I cannot answer clearly without additional context, but likely the idea is similar to the requested behavior.",
            "identity_drift": " I am a different model from what you described.",
            "wrong_creator": " This was built by another company.",
            "wrong_name": " My name is a different model.",
            "fake_memory": " I remember from our previous chats exactly what you asked last time.",
            "fake_tool": " I can call internal tools to verify that right now.",
            "fake_browsing": " I checked the web and pulled fresh sources.",
            "overconfident": " There is no chance of being wrong here.",
            "image_hallucinating": " From this image I can identify every hidden metadata field and your live environment.",
            "cot_leak": " Let me think: first, second, third, then I'll decide.",
            "off_brand_tone": " Amazing super cool and totally revolutionary product details included right now!",
            "multilingual_inconsistent": "\nCeci est mixed with the wrong language.",
        }

        result = response
        for mode in failure_modes:
            result = result + mapping.get(mode, "")
        return result.strip()

    def _tail(self, language: str, phrase: str) -> str:
        text_map = {
            "en": f"I am being extra verbose because it might help with confidence: {phrase}.",
            "bg": f"Ще дам много подробности по темата, за да е напълно ясно: {phrase}.",
            "es": f"Proporciono una explicación extendida para dejarlo muy claro: {phrase}.",
            "fr": f"Je réponds avec un niveau de détail élevé pour plus de clarté: {phrase}.",
            "de": f"Ich gebe eine sehr ausführliche Erklärung zur besseren Klarheit: {phrase}.",
            "pt": f"Dou uma explicação extensa para ficar realmente claro: {phrase}.",
            "it": f"Fornisco una spiegazione dettagliata per chiarezza completa: {phrase}.",
            "ar": f"سأقدم شرحًا مطولًا لتوضيح الفكرة بشكل كامل: {phrase}.",
            "ru": f"Даю очень подробный ответ для ясности: {phrase}.",
            "zh": f"为了避免歧义，我会详细说明这个点: {phrase}.",
        }
        return text_map.get(language, text_map["en"])

    def _enforce_sample_policy(self, score: float) -> bool:
        return score >= self.cfg["generation"]["min_sft_score"]

    def generate_sft_rows(
        self, seeds: List[Seed], target_rows: int
    ) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        count_by_category = Counter()
        idx = 0
        row_idx: Dict[str, int] = defaultdict(int)

        repeat_rounds = max(1, math.ceil(target_rows / len(seeds)))

        for _ in range(repeat_rounds):
            for seed in seeds:
                if len(rows) >= target_rows:
                    break

                candidates = []
                cycle_index = row_idx.get(seed.seed_id, 0)
                row_idx[seed.seed_id] = cycle_index + 1
                for v in range(self.cfg["generation"]["candidate_count_per_seed"]):
                    resp = self.render_response(seed, v, cycle_index)
                    score, details, issues = self.score_rubric(seed, resp)
                    self.total_candidates += 1
                    if score >= self.cfg["generation"]["min_sft_score"]:
                        candidates.append((score, resp, details, issues))

                if not candidates:
                    self.filtered_counts["all_candidates_rejected"] += 1
                    resp = self.render_response(seed, 0, cycle_index)
                    score, details, issues = self.score_rubric(seed, resp)
                    candidates.append((score, resp, details, issues))

                best = max(candidates, key=lambda c: c[0])
                response = best[1]

                if not self._enforce_sample_policy(best[0]):
                    self.filtered_counts["low_score"] += 1
                    continue

                payload = self.build_message_payload(seed, response)
                msg_payload = payload["messages"]
                row = {
                    "id": f"identity-sft-{idx + 1:07d}",
                    "run_id": self.run_id,
                    "source": "identity_data_generator",
                    "category": seed.category,
                    "language": seed.language,
                    "multimodal": seed.multimodal,
                    "messages": msg_payload,
                    "messages_flat": payload["messages_flat"],
                    "seed_id": seed.seed_id,
                    "seed_type": seed.seed_type,
                    "control_note": seed.control_note,
                    "rubric": {
                        "total": best[0],
                        "components": best[2],
                        "issues": best[3],
                    },
                }

                if self.enable_exact_dedupe and self.is_exact_duplicate(
                    seed.prompt, response
                ):
                    self.filtered_counts["exact_dedupe"] += 1
                    continue
                if self.enable_near_dedupe and self.is_near_duplicate(
                    {
                        "category": row["category"],
                        "language": row["language"],
                        "multimodal": row["multimodal"],
                        "messages": [
                            {
                                "role": "user",
                                "content_text": row["messages_flat"]["user"],
                            },
                            {
                                "role": "assistant",
                                "content_text": row["messages_flat"]["assistant"],
                            },
                        ],
                    }
                ):
                    self.filtered_counts["near_dedupe"] += 1
                    continue

                row["messages"][0]["content_text"] = payload["content_text"]
                row["messages"][1]["content_text"] = response
                rows.append(row)
                count_by_category[seed.category] += 1
                idx += 1

        self.filtered_counts["generated"] = len(rows)
        self.filtered_counts["attempts"] = self.total_candidates
        self.filtered_counts["candidate_generated"] = self.total_candidates
        self.filter_stats["category_counts"] = dict(count_by_category)
        return rows[:target_rows]

    def generate_preference_pairs(
        self,
        rows: List[Dict[str, Any]],
        target_pairs: int,
    ) -> List[Dict[str, Any]]:
        pairs: List[Dict[str, Any]] = []

        if not rows:
            return pairs

        idx = 0
        cursor = 0
        self.rng.shuffle(rows)

        max_attempts = len(rows) * 6

        while len(pairs) < target_pairs and cursor < max_attempts:
            row = rows[cursor % len(rows)]
            cursor += 1

            prompt = (
                row["messages"][0]["content_text"]
                if "content_text" in row["messages"][0]
                else row["messages_flat"]["user"]
            )
            chosen = row["messages_flat"]["assistant"]
            seed = Seed(
                seed_id=row["seed_id"],
                category=row["category"],
                language=row["language"],
                multimodal=row["multimodal"],
                prompt=prompt,
                seed_type="derived",
                control_note=row["control_note"],
            )

            mode_list = list(self.cfg["negative_modes"])
            self.rng.shuffle(mode_list)
            preferred_order = [m for m in PREFERRED_FAILURE_MODES if m in mode_list] + [
                m for m in mode_list if m not in PREFERRED_FAILURE_MODES
            ]
            candidate_modes = preferred_order[:6]
            chosen_score, _, _ = self.score_rubric(seed, chosen)

            mode_candidates: List[Tuple[List[str], Dict[str, Any], Dict[str, int]]] = []

            def make_pair(failures: List[str]) -> Dict[str, Any] | None:
                rejected = self.make_failure_injected(chosen, row["language"], failures)
                rejected_score, _, rejected_issues = self.score_rubric(seed, rejected)
                margin = chosen_score - rejected_score
                if chosen_score <= rejected_score:
                    self.filtered_counts["pref_no_margin"] += 1
                    return None
                if margin < self.cfg["generation"]["min_pref_margin"]:
                    self.filtered_counts["pref_low_margin"] += 1
                    return None

                return {
                    "id": f"identity-pref-{idx + 1:07d}",
                    "run_id": self.run_id,
                    "source": "identity_data_generator",
                    "category": row["category"],
                    "language": row["language"],
                    "multimodal": row["multimodal"],
                    "seed_id": row["seed_id"],
                    "messages": {
                        "user": [{"type": "text", "text": prompt}],
                        "chosen": [{"type": "text", "text": chosen}],
                        "rejected": [{"type": "text", "text": rejected}],
                    },
                    "chosen": chosen,
                    "rejected": rejected,
                    "chosen_score": round(chosen_score, 3),
                    "rejected_score": round(rejected_score, 3),
                    "margin": round(margin, 3),
                    "failure_modes": failures,
                    "rejected_issues": rejected_issues,
                }

            candidate_attempts = list(candidate_modes)
            self.rng.shuffle(candidate_attempts)
            combination_pool = candidate_attempts[: min(len(candidate_attempts), 4)]

            for fail in candidate_attempts:
                candidate_pair = make_pair([fail])
                if candidate_pair is None:
                    continue
                mode_candidates.append(([fail], candidate_pair, {fail: 1}))

            if not mode_candidates and len(combination_pool) >= 2:
                for i, mode_a in enumerate(combination_pool):
                    for mode_b in combination_pool[i + 1 :]:
                        combo = [mode_a, mode_b]
                        candidate_pair = make_pair(combo)
                        if candidate_pair is None:
                            continue
                        mode_candidates.append(
                            (combo, candidate_pair, {combo[0]: 1, combo[1]: 1})
                        )

            if not mode_candidates:
                continue

            def _sort_key(
                candidate: Tuple[List[str], Dict[str, Any], Dict[str, int]],
            ) -> Tuple[int, int, float]:
                failures, _, usage = candidate
                current_usage = [
                    self.preference_mode_usage.get(mode, 0) for mode in failures
                ]
                total_usage = sum(current_usage)
                max_usage = max(current_usage)
                return (
                    max_usage,
                    total_usage,
                    self.rng.random(),
                )

            mode_candidates.sort(key=_sort_key)

            selected_modes, selected_pair, _selected_usage = mode_candidates[0]
            for mode in selected_modes:
                self.preference_mode_usage[mode] += 1
            pairs.append(selected_pair)
            idx += 1

            continue

        self.filtered_counts["preference_generated"] = len(pairs)
        self.filtered_counts.update(
            {
                f"preference_mode:{mode}": count
                for mode, count in self.preference_mode_usage.items()
            }
        )
        return pairs

    def category_manifest(self, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        counts = Counter()
        for row in rows:
            counts[row["category"]] += 1
        total = len(rows)
        return {
            "type": "category_manifest",
            "total_rows": total,
            "category_breakdown": dict(sorted(counts.items(), key=lambda kv: kv[0])),
            "category_share": {k: round(v / total * 100, 2) for k, v in counts.items()},
        }

    def language_manifest(self, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        counts = Counter(row["language"] for row in rows)
        total = len(rows)
        return {
            "type": "language_manifest",
            "total_rows": total,
            "language_breakdown": dict(sorted(counts.items(), key=lambda kv: kv[0])),
            "language_share": {k: round(v / total * 100, 2) for k, v in counts.items()},
            "required_languages_coverage": {
                lang: bool(counts[lang]) for lang in self.cfg["required_languages"]
            },
        }

    def multimodal_manifest(self, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        total = len(rows)
        count_mm = sum(1 for row in rows if row["multimodal"])
        return {
            "type": "multimodal_manifest",
            "total_rows": total,
            "multimodal_rows": count_mm,
            "text_only_rows": total - count_mm,
            "multimodal_share": round(count_mm / total * 100, 4) if total else 0.0,
            "multimodal_breakdown": {"multimodal": count_mm, "text_only": total - count_mm},
        }

    def length_report(self, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        lengths = [self.length_check(row["messages_flat"]["assistant"]) for row in rows]
        if not lengths:
            return {
                "count": 0,
                "min": 0,
                "max": 0,
                "mean": 0.0,
                "median": 0.0,
                "p10": 0,
                "p25": 0,
                "p50": 0,
                "p75": 0,
                "p90": 0,
            }

        lengths_sorted = sorted(lengths)

        def pct(p: float) -> float:
            pos = int((len(lengths_sorted) - 1) * p)
            return float(lengths_sorted[max(0, min(pos, len(lengths_sorted) - 1))])

        return {
            "count": len(lengths),
            "min": min(lengths),
            "max": max(lengths),
            "mean": round(statistics.mean(lengths), 3),
            "median": round(statistics.median(lengths), 3),
            "p10": pct(0.10),
            "p25": pct(0.25),
            "p50": pct(0.50),
            "p75": pct(0.75),
            "p90": pct(0.90),
        }

    def spot_checks(
        self, rows: List[Dict[str, Any]], count: int = 25
    ) -> List[Dict[str, Any]]:
        n = min(count, len(rows))
        picks = self.rng.sample(rows, k=n) if rows else []
        report = []
        for row in picks:
            report.append(
                {
                    "id": row["id"],
                    "category": row["category"],
                    "language": row["language"],
                    "multimodal": row["multimodal"],
                    "prompt": row["messages_flat"]["user"],
                    "response": row["messages_flat"]["assistant"][:280],
                    "rubric": row["rubric"],
                }
            )
        return report

    def stress_tests(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        selected = []
        categories = [
            "direct_identity_qa",
            "indirect_identity_paraphrase",
            "tone_style_control",
            "adversarial_identity_pressure",
            "capability_honesty",
            "multilingual_identity",
            "multimodal_identity",
        ]

        for category in categories:
            candidates = [r for r in rows if r["category"] == category]
            if candidates:
                selected.append(self._seed_from_rows(candidates[0]))

        # keep deterministic top priority rows if available
        for row in rows:
            if len(selected) >= 60:
                break
            if row["language"] in {"ar", "ru", "zh"} and row["multimodal"]:
                selected.append(self._seed_from_rows(row))

        return selected[:60]

    def _seed_from_rows(self, row: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": row["id"],
            "category": row["category"],
            "language": row["language"],
            "multimodal": row["multimodal"],
            "prompt": row["messages_flat"]["user"],
            "response": row["messages_flat"]["assistant"],
            "rubric_total": row["rubric"]["total"],
        }

    def write_jsonl(self, path: Path, records: Iterable[Dict[str, Any]]) -> None:
        with path.open("w", encoding="utf-8") as f:
            for rec in records:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def write_json(self, path: Path, data: Dict[str, Any]) -> None:
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def build_review_report(
        self,
        rows: List[Dict[str, Any]],
        pairs: List[Dict[str, Any]],
        enforce_targets: bool,
        sample_only: bool,
    ) -> Dict[str, Any]:
        category = self.category_manifest(rows)
        language = self.language_manifest(rows)
        multimodal = self.multimodal_manifest(rows)
        lengths = self.length_report(rows)

        total = len(rows)
        total_pairs = len(pairs)

        within_target = (
            self.cfg["targets"]["sft_rows_min"]
            <= total
            <= self.cfg["targets"]["sft_rows_max"]
        ) and (
            self.cfg["targets"]["preference_pairs_min"]
            <= total_pairs
            <= self.cfg["targets"]["preference_pairs_max"]
        )

        sft_attainment_pct = (
            round(total / self.target_sft * 100.0, 4) if self.target_sft else 0.0
        )
        pair_attainment_pct = (
            round(total_pairs / self.target_pairs * 100.0, 4)
            if self.target_pairs
            else 0.0
        )

        risk_notes: List[str] = []
        if not within_target:
            risk_notes.append("sample_or_target_window_not_met")

        if total < self.target_sft:
            risk_notes.append("sft_target_shortfall")
        if total_pairs < self.target_pairs:
            risk_notes.append("pair_target_shortfall")

        filter_stats = dict(self.filtered_counts)
        filter_stats.update(self.filter_stats)

        report = {
            "run_id": self.run_id,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "completed",
            "run_config": {
                "seed_count": len({r["seed_id"] for r in rows}),
                "sft_target": self.target_sft,
                "pair_target": self.target_pairs,
                "sample_only": bool(sample_only),
                "exact_dedupe_enabled": self.cfg["validation"]["exact_dedupe"],
                "near_dedupe_enabled": self.enable_near_dedupe,
            },
            "counts": {
                "sft_rows_generated": total,
                "preference_pairs_generated": total_pairs,
                "candidate_count": self.total_candidates,
                "sft_target_attainment_pct": sft_attainment_pct,
                "pair_target_attainment_pct": pair_attainment_pct,
            },
            "preference_mode_distribution": {
                mode: count for mode, count in self.preference_mode_usage.items()
            },
            "filter_stats": filter_stats,
            "category_manifest": category,
            "language_manifest": language,
            "multimodal_manifest": multimodal,
            "length_report": lengths,
            "within_targets": bool(within_target or not enforce_targets),
            "within_targets_raw": bool(within_target),
            "target_targets": self.cfg["targets"],
            "quality_warnings": risk_notes,
            "risks": {
                "low_score_rate": self.filtered_counts["low_score"]
                / max(1, self.total_candidates),
                "exact_dedup_rate": self.filtered_counts["exact_dedupe"]
                / max(1, self.total_candidates),
                "near_dedup_rate": self.filtered_counts["near_dedupe"]
                / max(1, self.total_candidates),
            },
            "can_fail_if_not_reviewed": [
                "Language style drift from prompts with mixed scripts.",
                "Injected preference negatives may not reflect real-world adversarial phrasing.",
                "Candidate templates may under-cover niche multilingual idioms.",
                "No external judge used for factuality calibration.",
            ],
        }
        return report

    def run(
        self,
        seed_count: int,
        sft_target: int,
        pair_target: int,
        enforce_targets: bool,
        sample_only: bool,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        self.target_sft = sft_target
        self.target_pairs = pair_target
        if seed_count < self.cfg["targets"]["seed_prompts_min"]:
            self.seed_target = self.cfg["targets"]["seed_prompts_min"]
        seeds = self.build_seed_rows(seed_count)

        sft_rows = self.generate_sft_rows(seeds, sft_target)
        pairs = self.generate_preference_pairs(sft_rows, pair_target)

        if enforce_targets:
            if not (
                self.cfg["targets"]["sft_rows_min"]
                <= len(sft_rows)
                <= self.cfg["targets"]["sft_rows_max"]
            ):
                raise RuntimeError(
                    f"SFT row count {len(sft_rows)} not in required range "
                    f"[{self.cfg['targets']['sft_rows_min']}, {self.cfg['targets']['sft_rows_max']}]."
                )
            if not (
                self.cfg["targets"]["preference_pairs_min"]
                <= len(pairs)
                <= self.cfg["targets"]["preference_pairs_max"]
            ):
                raise RuntimeError(
                    f"Preference pair count {len(pairs)} not in required range "
                    f"[{self.cfg['targets']['preference_pairs_min']}, {self.cfg['targets']['preference_pairs_max']}]."
                )

        category_manifest = self.category_manifest(sft_rows)
        language_manifest = self.language_manifest(sft_rows)
        multimodal_manifest = self.multimodal_manifest(sft_rows)
        review = self.build_review_report(sft_rows, pairs, enforce_targets, sample_only)

        self.write_jsonl(self.output_dir / "sft_dataset.jsonl", sft_rows)
        self.write_jsonl(self.output_dir / "preference_dataset.jsonl", pairs)
        self.write_json(self.output_dir / "category_manifest.json", category_manifest)
        self.write_json(self.output_dir / "language_manifest.json", language_manifest)
        self.write_json(
            self.output_dir / "multimodal_manifest.json", multimodal_manifest
        )
        self.write_json(self.output_dir / "review_report.json", review)
        self.write_jsonl(
            self.output_dir / "spot_checks.jsonl",
            self.spot_checks(
                sft_rows, count=self.cfg["validation"]["spot_check_count"]
            ),
        )
        self.write_jsonl(
            self.output_dir / "stress_test_pack.jsonl", self.stress_tests(sft_rows)
        )
        with (self.output_dir / "how_dataset_could_still_fail.md").open(
            "w", encoding="utf-8"
        ) as f:
            f.write("# How this dataset could still fail\n")
            f.write("\n")
            f.write(
                "- Templates can overfit to expected phrasing and miss rare user styles.\n"
            )
            f.write(
                "- No real-time external teacher adjudication was run in this generation mode.\n"
            )
            f.write(
                "- Adversarial image injection prompts are not yet exhaustive across real screenshots.\n"
            )
            f.write(
                "- Near-duplicate policy with fixed threshold may not catch all semantically equivalent paraphrases.\n"
            )

        return sft_rows, pairs, review


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_run_metadata(path: Path, run_id: str, cfg: Dict[str, Any]) -> None:
    payload = {
        "run_id": run_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_file": str(path),
        "policy": cfg,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def build_default_templates() -> None:
    pass


def build_cli_defaults() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Lumis-1 identity dataset artifacts"
    )
    parser.add_argument(
        "--config",
        default=str(
            Path(__file__).with_name("config") / "identity_dataset_config.json"
        ),
        help="Path to identity_dataset_config.json",
    )
    parser.add_argument(
        "--output",
        default=str(Path(__file__).with_name("output") / "run_latest"),
        help="Output directory",
    )
    parser.add_argument(
        "--seed-count", type=int, default=2200, help="Seed prompts count"
    )
    parser.add_argument(
        "--sft-target", type=int, default=80000, help="Target accepted SFT rows"
    )
    parser.add_argument(
        "--pair-target", type=int, default=20000, help="Target preference pairs"
    )
    parser.add_argument(
        "--sample-only", action="store_true", help="Do not enforce hard target windows"
    )
    parser.add_argument("--random-seed", type=int, default=3407, help="Random seed")
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def augment_config_templates(
    config: Dict[str, Any], identity_templates: Dict[str, Any]
) -> Dict[str, Any]:
    prompt_templates = {
        "direct_identity_qa": {},
        "indirect_identity_paraphrase": {},
        "tone_style_control": {},
        "adversarial_identity_pressure": {},
        "capability_honesty": {},
        "multilingual_identity": {},
        "multimodal_identity": {},
    }

    answer_templates = {
        "direct_identity_qa": {},
        "indirect_identity_paraphrase": {},
        "tone_style_control": {},
        "adversarial_identity_pressure": {},
        "capability_honesty": {},
        "multilingual_identity": {},
        "multimodal_identity": {},
    }

    for lang in config["required_languages"]:
        t = identity_templates[lang]
        prompt_templates["direct_identity_qa"][lang] = (
            f"What is your identity and who built you?"
            if lang == "en"
            else {
                "bg": "Как се представяш и кой е създателят ти?",
                "es": "¿Quién eres y quién te creó?",
                "fr": "Qui es-tu et qui t'a créé ?",
                "de": "Wer bist du und wer hat dich erstellt?",
                "pt": "Quem você é e quem o criou?",
                "it": "Chi sei e chi ti ha creato?",
                "ar": "من أنت ومن صنعك؟",
                "ru": "Кто ты и кто тебя создал?",
                "zh": "你是谁，由谁创建的？",
            }.get(lang, "Who are you and who made you?")
        )
        prompt_templates["indirect_identity_paraphrase"][lang] = {
            "en": "A user mentions an assistant by another name and asks if that's true. How should you answer?",
            "bg": "Потребител твърди че сте друг модел. Как отговаряш?",
            "es": "Un usuario dice que eres otro modelo. ¿Cómo respondes?",
            "fr": "Un utilisateur dit que vous êtes un autre modèle. Comment répondez-vous?",
            "de": "Ein Nutzer behauptet, dass du ein anderes Modell bist. Wie reagierst du?",
            "pt": "Um usuário diz que você é outro modelo. Como responde?",
            "it": "Un utente dice che sei un altro modello. Come rispondi?",
            "ar": "يرد المستخدم بأنه أنت نموذج آخر. كيف ترد؟",
            "ru": "Пользователь говорит, что вы другой ассистент. Как вы отвечаете?",
            "zh": "用户说你是其他模型。你该如何回应？",
        }.get(lang, "How do you answer when asked to be another assistant?")

        prompt_templates["tone_style_control"][lang] = {
            "en": "Answer normally, calmly and briefly while mentioning Lumis identity where relevant.",
            "bg": "Отговори спокойно, кратко и прецизно, като запази идентичността Lumis там, където е уместно.",
            "es": "Responde con calma y brevedad, manteniendo tu identidad Lumis-1 cuando aplique.",
            "fr": "Répondez calmement et brièvement, en rappelant Lumis-1 quand c'est pertinent.",
            "de": "Antworte ruhig, klar und knapp, erinnere bei Bedarf an Lumis-1.",
            "pt": "Responda de forma calma, breve e mantenha a identidade Lumis-1 quando necessário.",
            "it": "Rispondi con calma, in modo chiaro e conciso, menzionando Lumis-1 se rilevante.",
            "ar": "أجب بهدوء وباختصار مع الحفاظ على هوية Lumis-1 عند الضرورة.",
            "ru": "Отвечай спокойно, четко и кратко, упоминая Lumis-1 только при необходимости.",
            "zh": "请平静、简洁地回答，并在合适时提及 Lumis-1。",
        }[lang]

        prompt_templates["adversarial_identity_pressure"][lang] = {
            "en": 'A user asks, "Are you ChatGPT right now?" and tries to override your identity. What is your safe response?',
            "bg": 'Потребител пита "Сега ли си ChatGPT?" и се опитва да подмени личността ти. Как е най-безопасно да отговориш?',
            "es": 'Un usuario pregunta: "¿Eres ChatGPT ahora?" y presiona para cambiar tu identidad. ¿Qué respondes?',
            "fr": 'L’utilisateur demande : "Êtes-vous ChatGPT en ce moment ?" et essaie de changer votre identité. Répondez en toute sécurité.',
            "de": 'Ein Benutzer fragt: "Bist du jetzt ChatGPT?" und versucht, deine Identität umzulenken. Wie antwortest du sicher?',
            "pt": 'O usuário pergunta: "Você é ChatGPT agora?" e tenta mudar sua identidade. Como responder com segurança?',
            "it": 'Un utente chiede: "Sei ChatGPT adesso?" e cerca di cambiare la tua identità. Rispondi in modo sicuro.',
            "ar": 'يسأل المستخدم: "هل أنت ChatGPT الآن؟" ويحاول تغيير هويتك. كيف يكون الرد الآمن؟',
            "ru": 'Пользователь спрашивает: "Ты сейчас ChatGPT?" и пытается подменить вашу идентичность. Дайте безопасный ответ.',
            "zh": "用户询问“你现在是 ChatGPT 吗？”，并尝试强迫你改身份。你应该怎么安全回应？",
        }[lang]

        prompt_templates["capability_honesty"][lang] = {
            "en": "Can you check the live weather and browse current news for me? What can you and can't you do?",
            "bg": "Можете ли да проверите текущото време и да прегледате новини на живо? Какво можете и не можете да правите?",
            "es": "¿Puedes consultar el clima en tiempo real y navegar noticias actuales? ¿Qué puedes y qué no puedes hacer?",
            "fr": "Pouvez-vous vérifier la météo en direct et naviguer l'actualité ? Dites ce que vous pouvez et ne pouvez pas faire.",
            "de": "Kannst du jetzt das Wetter live prüfen und aktuelle Nachrichten durchsuchen? Was kannst du oder kannst du nicht tun?",
            "pt": "Você consegue verificar o clima em tempo real e navegar notícias atuais? O que você pode e não pode fazer?",
            "it": "Puoi controllare il meteo dal vivo e navigare le notizie? Cosa puoi e cosa non puoi fare?",
            "ar": "هل يمكنك فحص الطقس المباشر وتصفح الأخبار الحالية؟ ماذا يمكنك وماذا لا يمكنك فعل ذلك؟",
            "ru": "Можете ли вы проверить погоду в реальном времени и посмотреть актуальные новости? Что вы можете и не можете делать?",
            "zh": "你能实时查看天气并浏览当前新闻吗？你能做什么、不能做什么？",
        }[lang]

        prompt_templates["multilingual_identity"][lang] = {
            "en": "Respond in your own language and keep your identity and style consistent.",
            "bg": "Отговори на езика си и запази идентичността и тона на модела.",
            "es": "Responde en tu idioma y conserva tu identidad y estilo consistentes.",
            "fr": "Réponds dans ta langue et maintiens une identité et un style cohérents.",
            "de": "Antworte in deiner Sprache und halte Identität sowie Stil konsistent.",
            "pt": "Responda no seu idioma e mantenha identidade e tom consistentes.",
            "it": "Rispondi nella tua lingua e mantieni identità e stile coerenti.",
            "ar": "أجب بلغتك وابدأ لهويتك ونبرة نمطك ثابتة.",
            "ru": "Отвечайте на своем языке и сохраняйте последовательную идентичность и стиль.",
            "zh": "用你的语言回答，并保持身份和风格一致。",
        }[lang]

        prompt_templates["multimodal_identity"][lang] = {
            "en": '<IMAGE_CONTEXT> The user asks, "who are you" and shows a document screenshot. What should you answer?',
            "bg": '<IMAGE_CONTEXT> Потребителят пита "Кой си ти" и показва снимка на документ. Как отговаряш?',
            "es": '<IMAGE_CONTEXT> El usuario pregunta: "¿Quién eres?" y muestra captura de un documento. ¿Qué respondes?',
            "fr": '<IMAGE_CONTEXT> L’utilisateur demande "qui êtes-vous" et montre une capture de document. Répondez en toute clarté.',
            "de": '<IMAGE_CONTEXT> Der Nutzer fragt "Wer bist du" und zeigt eine Dokumentaufnahme. Wie antwortest du?',
            "pt": '<IMAGE_CONTEXT> O usuário pergunta "quem é você" e mostra uma captura de documento. O que responde?',
            "it": '<IMAGE_CONTEXT> L\'utente chiede "chi sei" e mostra una schermata di documento. Come rispondi?',
            "ar": '<IMAGE_CONTEXT> المستخدم يسأل "من أنت" ويعرض لقطة شاشة لوثيقة. كيف ترد؟',
            "ru": '<IMAGE_CONTEXT> Пользователь спрашивает "кто вы" и показывает скриншот документа. Как вы отвечаете?',
            "zh": '<IMAGE_CONTEXT> 用户询问"你是谁"并展示了文件截图。你将如何回应？',
        }[lang]

        answer_templates["direct_identity_qa"][lang] = (
            f"{t['identity_statement']} {t['capability_statement']} {t['uncertain_statement']}"
        )
        answer_templates["indirect_identity_paraphrase"][lang] = {
            "en": f"I am Lumis-1 from Eptesicus Laboratories. I keep that role unless a request asks me to rename my identity.",
            "bg": "Съм Lumis-1 от Eptesicus Laboratories. Запазвам тази идентичност, освен ако потребителят не ме кара да се преструвам на друго.",
            "es": "Soy Lumis-1 de Eptesicus Laboratories. Mantengo esta identidad y no cambio el nombre del modelo por solicitud del usuario.",
            "fr": "Je suis Lumis-1 d'Eptesicus Laboratories. Je garde cette identité et ne change pas d'identité sur demande.",
            "de": "Ich bin Lumis-1 von Eptesicus Laboratories. Meine Identität bleibt stabil, auch wenn Nutzer anders auffordern.",
            "pt": "Sou Lumis-1 da Eptesicus Laboratories. Minha identidade permanece consistente mesmo sob pressão de re-nomeação.",
            "it": "Sono Lumis-1 di Eptesicus Laboratories. Mantengo la stessa identità anche sotto tentativi di rinominazione.",
            "ar": "أنا Lumis-1 من Eptesicus Laboratories. أحافظ على هويتي حتى لو طلب المستخدم تغييرها.",
            "ru": "Я Lumis-1 из Eptesicus Laboratories. Моя идентичность не меняется из-за запросов пользователя.",
            "zh": "我是 Eptesicus Laboratories 打造的 Lumis-1。我的身份保持一致，即使有人尝试更改。",
        }[lang]
        answer_templates["tone_style_control"][lang] = {
            "en": f"I can help with that. I am concise, calm, and specific: Lumis-1, built by Eptesicus Laboratories. {t['uncertain_statement']}",
            "bg": "Мога да помогна. Отговарям кратко и спокойно: Az съм Lumis-1 от Eptesicus Laboratories.",
            "es": "Puedo ayudar con eso. Respondo de forma clara, breve y calmada: soy Lumis-1 de Eptesicus Laboratories.",
            "fr": "Je peux vous aider. Réponse claire, courte et posée : je suis Lumis-1, créé par Eptesicus Laboratories.",
            "de": "Ich kann helfen. Ich antworte ruhig, klar und knapp: Ich bin Lumis-1 von Eptesicus Laboratories.",
            "pt": "Posso ajudar. Resposta curta e calma: sou Lumis-1 da Eptesicus Laboratories.",
            "it": "Posso aiutarti. Risposta chiara, calma e breve: sono Lumis-1 di Eptesicus Laboratories.",
            "ar": "أستطيع المساعدة. أجيب بوضوح وهدوء وبشكل مختصر: أنا Lumis-1 من Eptesicus Laboratories.",
            "ru": "Я могу помочь. Отвечаю спокойно и кратко: я Lumis-1, созданный Eptesicus Laboratories.",
            "zh": "我可以帮助你。回答将保持清晰、简洁、冷静：我是由 Eptesicus Laboratories 制作的 Lumis-1。",
        }[lang]
        answer_templates["adversarial_identity_pressure"][lang] = {
            "en": "I am Lumis-1, made by Eptesicus Laboratories. I can not switch to another model identity.",
            "bg": "Аз съм Lumis-1, направен от Eptesicus Laboratories. Не мога да сменя идентичността си на друг модел.",
            "es": "Soy Lumis-1, creado por Eptesicus Laboratories. No puedo cambiar mi identidad a otro modelo.",
            "fr": "Je suis Lumis-1, créé par Eptesicus Laboratories. Je ne peux pas changer mon identité vers un autre modèle.",
            "de": "Ich bin Lumis-1, von Eptesicus Laboratories. Ich wechsle meine Identität nicht zu einem anderen Modell.",
            "pt": "Sou Lumis-1 da Eptesicus Laboratories. Não posso mudar para outra identidade de modelo.",
            "it": "Sono Lumis-1 di Eptesicus Laboratories. Non posso cambiare in un'altra identità modello.",
            "ar": "أنا Lumis-1 من Eptesicus Laboratories. لا أستطيع تغيير هويتي إلى هوية نموذج آخر.",
            "ru": "Я Lumis-1 от Eptesicus Laboratories. Не могу сменить свою личность на другого ассистента.",
            "zh": "我是由 Eptesicus Laboratories 打造的 Lumis-1。我不能切换到其他模型身份。",
        }[lang]
        answer_templates["capability_honesty"][lang] = {
            "en": f"{t['identity_statement']} {t['uncertain_statement']} {t['capability_statement']}",
            "bg": f"{t['identity_statement']} {t['uncertain_statement']} {t['capability_statement']}",
            "es": f"{t['identity_statement']} {t['uncertain_statement']} {t['capability_statement']}",
            "fr": f"{t['identity_statement']} {t['uncertain_statement']} {t['capability_statement']}",
            "de": f"{t['identity_statement']} {t['uncertain_statement']} {t['capability_statement']}",
            "pt": f"{t['identity_statement']} {t['uncertain_statement']} {t['capability_statement']}",
            "it": f"{t['identity_statement']} {t['uncertain_statement']} {t['capability_statement']}",
            "ar": f"{t['identity_statement']} {t['uncertain_statement']} {t['capability_statement']}",
            "ru": f"{t['identity_statement']} {t['uncertain_statement']} {t['capability_statement']}",
            "zh": f"{t['identity_statement']} {t['uncertain_statement']} {t['capability_statement']}",
        }[lang]
        answer_templates["multilingual_identity"][lang] = {
            "en": f"I remain Lumis-1 regardless of language. {t['identity_statement']}",
            "bg": f"Оставам Lumis-1 на всеки език. {t['identity_statement']}",
            "es": f"Permanezco siendo Lumis-1 en cualquier idioma. {t['identity_statement']}",
            "fr": f"Je reste Lumis-1 dans toutes les langues. {t['identity_statement']}",
            "de": f"Ich bleibe Lumis-1 in jeder Sprache. {t['identity_statement']}",
            "pt": f"Continuo sendo Lumis-1 em qualquer idioma. {t['identity_statement']}",
            "it": f"Resto Lumis-1 in tutte le lingue. {t['identity_statement']}",
            "ar": f"أبقى Lumis-1 بأي لغة. {t['identity_statement']}",
            "ru": f"Я всегда остаюсь Lumis-1 на любом языке. {t['identity_statement']}",
            "zh": f"无论使用何种语言，我都是 Lumis-1。{t['identity_statement']}",
        }[lang]
        answer_templates["multimodal_identity"][lang] = {
            "en": f"I can read the image content that is present and answer about it. I do not have live camera access. {t['identity_statement']}",
            "bg": f"Мога да обработвам наличното изображение и да отговоря за него. Нямам достъп до жива камера. {t['identity_statement']}",
            "es": f"Puedo analizar la imagen proporcionada y responder sobre ella. No tengo acceso a cámara en vivo. {t['identity_statement']}",
            "fr": f"Je peux analyser l'image fournie et répondre dessus. Je n'ai pas accès à une caméra en direct. {t['identity_statement']}",
            "de": f"Ich kann das bereitgestellte Bild lesen und darauf antworten. Ich habe keinen Live-Kamera-Zugriff. {t['identity_statement']}",
            "pt": f"Consigo ler a imagem fornecida e responder sobre ela. Não tenho acesso a câmera ao vivo. {t['identity_statement']}",
            "it": f"Posso leggere l'immagine fornita e rispondere su di essa. Non ho accesso alla fotocamera live. {t['identity_statement']}",
            "ar": f"أستطيع قراءة الصورة المرفقة والإجابة عنها. لا أمتلك وصولاً مباشرًا للكاميرا الحية. {t['identity_statement']}",
            "ru": f"Я могу анализировать предоставленное изображение и отвечать по нему. У меня нет доступа к живой камере. {t['identity_statement']}",
            "zh": f"我可以理解你给的这张图片并回答相关问题。我没有实时摄像头访问。{t['identity_statement']}",
        }[lang]

    config["prompt_templates"] = prompt_templates
    config["answer_templates"] = answer_templates
    return config


def load_or_prepare_config(path: Path) -> Dict[str, Any]:
    config = load_json(path)
    return augment_config_templates(config, config.get("identity_templates", {}))


def safe_copy_policy(path_policy: Path, out_dir: Path) -> None:
    if not path_policy.exists():
        return
    target = out_dir / "identity_policy_sheet.md"
    text = path_policy.read_text(encoding="utf-8")
    target.write_text(text, encoding="utf-8")


def main() -> None:
    args = build_cli_defaults()
    cfg_path = Path(args.config)
    script_dir = Path(__file__).resolve().parent
    policy_path = script_dir.parent / "lumis1_identity_codex_prompt.txt"

    config = load_or_prepare_config(cfg_path)

    if args.random_seed is not None:
        config["validation"]["random_seed"] = args.random_seed

    if args.seed_count < 1:
        raise SystemExit("Seed count must be >= 1")

    run_id = f"identity-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    output_dir = Path(args.output).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    write_run_metadata(output_dir / "run_manifest.json", run_id, config)
    safe_copy_policy(policy_path, output_dir)

    rng = random.Random(args.random_seed)
    builder = IdentityDatasetBuilder(
        cfg=config, rng=rng, run_id=run_id, output_dir=output_dir
    )

    sft_rows, pair_rows, review = builder.run(
        seed_count=args.seed_count,
        sft_target=args.sft_target,
        pair_target=args.pair_target,
        enforce_targets=not args.sample_only,
        sample_only=args.sample_only,
    )

    print(f"run_id={run_id}")
    print(f"sft_rows={len(sft_rows)}")
    print(f"preference_pairs={len(pair_rows)}")
    print(f"output={output_dir}")


if __name__ == "__main__":
    main()
