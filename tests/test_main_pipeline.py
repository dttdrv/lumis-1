from __future__ import annotations

import json
from pathlib import Path

from lumis1.main_pipeline import (
    analyze_sft_training_surface,
    build_gguf_export_plan,
    build_main_colab_run_plan,
    materialize_text_only_training_dataset,
    resolve_dpo_runtime,
    resolve_sft_runtime,
)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    _write_text(
        repo / "configs" / "train_sft.yaml",
        "\n".join(
            [
                'model:',
                '  base_model: "Qwen/Qwen3.5-4B"',
                '  dtype: "bf16"',
                '  load_in_4bit: false',
                'lora:',
                '  r: 32',
                '  lora_alpha: 64',
                '  lora_dropout: 0.0',
                '  bias: "none"',
                '  target_modules: ["q_proj"]',
                'training:',
                '  max_steps: 3000',
                '  bf16: true',
                'sanity_run:',
                '  max_steps: 50',
                'datasets:',
                '  train_sft_path: "workspace/final/full_sft.jsonl"',
                'outputs:',
                '  run_dir: "workspace/runs/manual-sft/artifacts/sft_model"',
                '  checkpoint_dir: "workspace/runs/manual-sft/artifacts/sft_model/checkpoints"',
                "",
            ]
        ),
    )
    _write_text(
        repo / "configs" / "train_dpo.yaml",
        "\n".join(
            [
                'model:',
                '  base_model: "Qwen/Qwen3.5-4B"',
                '  sft_checkpoint_or_adapter: "workspace/runs/manual-sft/artifacts/sft_model"',
                '  dtype: "bf16"',
                '  load_in_4bit: false',
                'lora:',
                '  r: 32',
                '  lora_alpha: 64',
                '  lora_dropout: 0.0',
                '  bias: "none"',
                'training:',
                '  max_steps: 2000',
                '  bf16: true',
                'dpo:',
                '  beta: 0.1',
                'preferences:',
                '  optional_additional_preferences:',
                '    enabled: false',
                'outputs:',
                '  run_dir: "workspace/runs/manual-dpo/artifacts/dpo_model"',
                "",
            ]
        ),
    )
    _write_text(
        repo / "configs" / "run_profiles.yaml",
        "\n".join(
            [
                'profiles:',
                '  default_96gb:',
                '    sft:',
                '      gradient_accumulation_steps: 16',
                '    dpo:',
                '      gradient_accumulation_steps: 16',
                "",
            ]
        ),
    )
    _write_text(
        repo / "configs" / "chat_template_policy.yaml",
        "\n".join(
            [
                'allowed_template:',
                '  expected_chat_template_kwargs:',
                '    enable_thinking: false',
                "",
            ]
        ),
    )
    return repo


def test_build_main_colab_run_plan_sanitizes_prefix_and_creates_expected_paths(
    tmp_path: Path,
) -> None:
    repo = _make_repo(tmp_path)
    plan = build_main_colab_run_plan(repo, "Colab Main 01")

    assert plan["run_prefix"] == "colab-main-01"
    assert plan["sft_run_id"] == "colab-main-01-sft"
    assert plan["dpo_run_id"] == "colab-main-01-dpo"
    assert plan["export_run_id"] == "colab-main-01-export"
    assert plan["eval_run_id"] == "colab-main-01-eval"
    assert plan["sft_output_dir"] == repo / "workspace" / "runs" / "colab-main-01-sft" / "artifacts" / "sft_model"
    assert plan["dpo_output_dir"] == repo / "workspace" / "runs" / "colab-main-01-dpo" / "artifacts" / "dpo_model"
    assert plan["gguf_dir"] == repo / "workspace" / "runs" / "colab-main-01-export" / "artifacts" / "gguf"


def test_resolve_sft_runtime_uses_run_plan_and_sanity_override(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    plan = build_main_colab_run_plan(repo, "demo")

    resolved = resolve_sft_runtime(
        repo,
        run_plan=plan,
        profile_name="default_96gb",
        run_training=True,
        first_50_steps_sanity=True,
    )

    assert resolved["run_id"] == "demo-sft"
    assert resolved["output_dir"] == str(plan["sft_output_dir"])
    assert resolved["checkpoint_dir"] == str(plan["sft_checkpoint_dir"])
    assert resolved["dataset_path"] == str(repo / "workspace" / "final" / "full_sft.jsonl")
    assert resolved["run_training"] is True
    assert resolved["training"]["max_steps"] == 50
    assert resolved["training"]["gradient_accumulation_steps"] == 16


def test_resolve_dpo_runtime_uses_sft_output_from_run_plan(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    plan = build_main_colab_run_plan(repo, "demo")

    resolved = resolve_dpo_runtime(
        repo,
        run_plan=plan,
        profile_name="default_96gb",
        run_training=False,
    )

    assert resolved["run_id"] == "demo-dpo"
    assert resolved["output_dir"] == str(plan["dpo_output_dir"])
    assert resolved["sft_checkpoint_or_adapter"] == str(plan["sft_output_dir"])
    assert resolved["run_training"] is False
    assert resolved["training"]["gradient_accumulation_steps"] == 16


def test_build_gguf_export_plan_defaults_to_q8_and_q4(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    plan = build_main_colab_run_plan(repo, "demo")

    export = build_gguf_export_plan(
        model_dir=plan["dpo_output_dir"],
        export_dir=plan["gguf_dir"],
    )

    assert export["model_dir"] == plan["dpo_output_dir"]
    assert export["export_dir"] == plan["gguf_dir"]
    assert export["quantization_methods"] == ["q8_0", "q4_k_m"]
    assert export["zip_path"] == plan["gguf_dir"].parent / "gguf_bundle.zip"


def test_analyze_sft_training_surface_detects_placeholder_only_multimodal_rows(
    tmp_path: Path,
) -> None:
    dataset_path = tmp_path / "full_sft.jsonl"
    dataset_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "id": "row-1",
                        "modality": "multimodal",
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": "A screenshot is provided."},
                                    {"type": "image", "image": "image://seed-0001.jpg"},
                                ],
                            },
                            {"role": "assistant", "content": "I am Lumis-1."},
                        ],
                    }
                ),
                json.dumps(
                    {
                        "id": "row-2",
                        "modality": "text",
                        "messages": [
                            {"role": "user", "content": "Hello"},
                            {"role": "assistant", "content": "Hi"},
                        ],
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report = analyze_sft_training_surface(dataset_path)

    assert report["row_count"] == 2
    assert report["multimodal_rows"] == 1
    assert report["placeholder_image_rows"] == 1
    assert report["concrete_image_rows"] == 0
    assert report["training_surface"] == "text_only_placeholder_fallback"


def test_materialize_text_only_training_dataset_strips_placeholder_image_blocks(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "full_sft.jsonl"
    output_path = tmp_path / "prepared.jsonl"
    source_path.write_text(
        json.dumps(
            {
                "id": "row-1",
                "modality": "multimodal",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "A screenshot is provided."},
                            {"type": "image", "image": "synthetic://doc.png"},
                        ],
                    },
                    {
                        "role": "assistant",
                        "content": [{"type": "text", "text": "I can help with that."}],
                    },
                ],
                "meta": {"language": "en"},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = materialize_text_only_training_dataset(source_path, output_path)
    rows = [
        json.loads(line)
        for line in output_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert report["training_surface"] == "text_only_placeholder_fallback"
    assert report["transformed_multimodal_rows"] == 1
    assert rows[0]["modality"] == "text"
    assert rows[0]["messages"][0]["content"] == "A screenshot is provided."
    assert rows[0]["messages"][1]["content"] == "I can help with that."
    assert rows[0]["meta"]["multimodal_placeholder_collapsed_for_training"] is True
