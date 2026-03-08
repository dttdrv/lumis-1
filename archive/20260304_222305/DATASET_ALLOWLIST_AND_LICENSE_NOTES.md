# Dataset Allowlist and License Notes

Purpose: define lawful candidate sources for the non-identity 80% of the corpus and explicit exclusion rules.

## Hard policy

- Exclude leaked/private/proprietary/access-controlled corpora.
- Exclude raw chain-of-thought, raw `<think>` traces, raw reasoning content, and internal lab traces as direct targets.
- Exclude any source or subset with unclear commercial redistribution rights.
- If license or subset rights are unclear: skip and record the skip.

## Allowed candidate sources (subject to filtering and subset checks)

### Polished general assistant / instruction-following

- `HuggingFaceTB/smoltalk` (Apache-2.0)
- `HuggingFaceTB/smoltalk2` (Apache-2.0; prefer no_think subsets where available)
- `HuggingFaceH4/ultrachat_200k` (MIT)

### Real-user conversations

- `allenai/WildChat-1M` (ODC-By; require strict quality/safety filtering)

### Multilingual

- `CohereLabs/aya_dataset` (CC-BY-NC-4.0 from card metadata)
- Select multilingual subsets from SmolTalk/SmolTalk2 that pass no-think and quality constraints.

### Preference data for DPO

- Identity preference pairs from canonical identity pack (first-class, fixed slice)
- `argilla/ultrafeedback-binarized-preferences-cleaned` (MIT)
- Select lawful no-think preference subsets from SmolTalk2 or equivalent with clear rights.

### Multimodal overlay candidates

- `HuggingFaceM4/Docmatix` (CDLA-Permissive-2.0)
- `facebook/textvqa` (CC-BY-4.0 on card metadata)
- `lmms-lab/DocVQA` (Apache-2.0 on card metadata)
- `HuggingFaceM4/the_cauldron` (mixed; include only subset-cleared components)

## Restricted / caution flags

- `CohereLabs/aya_dataset`: card metadata indicates non-commercial license (`CC-BY-NC-4.0`); this is a commercial-risk flag for downstream productization unless legal explicitly approves.
- `HuggingFaceM4/the_cauldron`: mixed-source composition. Only include subsets with verified admissible license and terms.
- `allenai/WildChat-1M`: conversation data may include low-quality or policy-unsafe content; heavy filtering is mandatory.

## Transformation policy for reasoning-heavy sources

A reasoning-heavy source is admissible only when all are true:

1. License is acceptable for intended use.
2. Target output is transformed into concise non-thinking answer style.
3. Transformed target is labeled as transformed.
4. Raw reasoning text is removed from training targets.
5. Transformation pipeline is reproducible and documented.

If any condition fails, source rows are skipped.
