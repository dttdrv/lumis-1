from __future__ import annotations

from pathlib import Path

from lumis1.export_smoke import run_export_smoke


def test_run_export_smoke_passes_with_required_variants_and_parity(tmp_path: Path) -> None:
    export_dir = tmp_path / "export"
    export_dir.mkdir()
    (export_dir / "model-q8_0.gguf").write_bytes(b"q8")
    (export_dir / "model-q4_k_m.gguf").write_bytes(b"q4")

    report = run_export_smoke(
        export_dir,
        [
            {
                "prompt": "Hello",
                "hf_output": "Lumis answers directly",
                "gguf_output": "Lumis answers directly",
            }
        ],
    )

    assert report["ok"] is True
    assert report["variants"]["has_q8_0"] is True
    assert report["variants"]["has_q4_candidate"] is True
