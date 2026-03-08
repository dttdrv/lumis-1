# Lumis-1 Identity Dataset Pipeline (Identity-Only)

This directory contains a scaffold for generating the **identity and behavior dataset only** for Lumis-1.

## What this produces
- Canonical policy sheet and config for identity data generation.
- Deterministic SFT rows in a single JSONL schema.
- Preference `chosen/rejected` pairs with controlled failures.
- Category manifest, language manifest, multimodal manifest.
- Review report with dedupe/length/lang checks and stress test pack.

## How to run
- Generate a small verification sample:
  - `python identity_dataset_builder.py --output output/sample_run --sft-target 1000 --pair-target 250 --seed-count 120 --sample-only`
- Generate full identity dataset target:
  - `python identity_dataset_builder.py --output output/full_run --sft-target 100000 --pair-target 25000`

The generator is designed for offline reproducibility and does not call any external API.
Use external teacher calls only if you implement a custom provider plug-in.
