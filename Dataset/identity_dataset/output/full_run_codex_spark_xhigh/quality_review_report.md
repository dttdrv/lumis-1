# Quality Review Report — identity_dataset/output/full_run_codex_spark_xhigh

Scope reviewed: `state.json`, final datasets, manifests, dedupe ledger, review logs, and heartbeat/status files.

Findings (conclusive):

1. PASS — Run completion and counts
- `run_id`: `identity-20260303T162023Z`
- `state.json`: `status=finalized`, `sft_written=100000`, `pref_written=25000`, `next_chunk=101`
- Final datasets: `sft_dataset.jsonl=100000` rows, `preference_dataset.jsonl=25000` rows
- `run_manifest.json`: `sft_rows=100000`, `preference_pairs=25000`

2. PASS — Required languages
- Required language set all present in `language_manifest.json`: `en, bg, es, fr, de, pt, it, ar, ru, zh`

3. PASS — Schema and parser integrity signals
- `review_logs/review_final_sft.json`: approved, `invalid_lines=0`
- `review_logs/review_final_pref.json`: approved, `invalid_lines=0`
- `review_logs/review_final_report.json`: approved
- `sft` required top-level fields observed: `id, run_id, source, category, language, multimodal, messages, messages_flat, seed_id, seed_type, control_note, rubric`
- `preference` required top-level fields observed: `id, run_id, source, category, language, multimodal, seed_id, messages, chosen, rejected, chosen_score, rejected_score, margin, failure_modes, rejected_issues`

4. PASS — Duplicate and dedupe checks
- Exact `id` duplicates in SFT: `0`
- Exact prompt+assistant signature duplicates (SFT via `messages_flat`): `0`
- Preference duplicate signature rough check: `0`
- `dedupe_exact.sha256.txt` exists with `125000` lines (matches total accepted rows)

5. PASS — Policy/compliance score gates
- Preference rows with `chosen_score <= rejected_score`: `0`
- Preference rows with `margin < 0.8`: `0`
- Preference `failure_modes` outside allowed set: `0`

6. PASS — Distribution controls
- Category shares sum to `100.0%` (`multimodal_identity 10.06`, `direct_identity_qa 19.59`, `indirect_identity_paraphrase 19.99`, `tone_style_control 15.18`, `adversarial_identity_pressure 14.92`, `capability_honesty 10.05`, `multilingual_identity 10.21`)
- Language shares sum to `100.01%` (floating-point rounding artifact)

7. PASS — Obvious red-flag scan
- CoT-like phrase markers in accepted SFT answers: `0`
- Rejected preference responses with CoT-like markers: `8360` (expected; these are rejected samples by design)
- No brand-identity mentions missing in accepted outputs:
  - SFT without `Lumis-1`/`Eptesicus` in assistant text: `0`
  - Preference chosen responses without brand mentions: `0`

Minor non-blocking observations:
- `heartbeat.log` contains a historical line with `status="fatal"` while no fatal chunk artifacts exist and final state is `finalized`; this appears to be a pre-finalization heartbeat write, not a terminal failure.

Recommendation:
- No blocking policy/compliance defects found for the finalized run.
