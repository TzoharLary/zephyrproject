---
name: group-b-content-authoring
description: Create or update Group_B_data Logic/Structure markdown files for BPS/WSS/SCPS using the structured blocks schema (groupb_finding/source_observation/method/open_question), with source traceability, confidence, and phase-1 subset decisions.
---

# Group B Content Authoring

Use this skill when editing:
- `tools/templates/pts_report_he/Group_B_data/Logic/*.md`
- `tools/templates/pts_report_he/Group_B_data/Structure/*.md`

## Goal

Keep `Group_B_data` as a reliable storage layer for the Hub's normalized knowledge model.

## Required structure

Every file must keep:
- YAML front matter (profile_id, doc_kind, status, updated_at, language, schema_version)
- Required `##` sections for its kind
- Structured fenced blocks with valid JSON only:
  - `groupb_finding`
  - `groupb_source_observation`
  - `groupb_method`
  - `groupb_open_question`

## Authoring rules

1. Every `groupb_finding` must include:
- `confidence`
- `status`
- `source_ids[]`
- `derivation_method_ids[]`

2. Every `groupb_source_observation` must include:
- `source_id`
- `what_identified_he`
- `how_identified_he`
- `artifact_ref`
- `confidence`

3. Prefer explicit `line_refs` in observations and evidence refs.

4. Keep Hebrew explanations in UI-facing text fields.
- English only for identifiers, code, paths, APIs, spec terms.

5. Add at least one explicit Phase 1 subset decision per profile (logic or structure).

## Anti-patterns (avoid)

- Claim without `source_ids`
- `confidence: high` on inferred claim without detailed evidence
- Raw markdown prose that duplicates the structured finding without adding value
- Reusing source IDs that are not in source catalogs

## Standard workflow

1. Edit one profile at a time (`BPS`, then `WSS`, then `SCPS`)
2. Run:
   - `python tools/check_group_b_hub.py`
3. Rebuild:
   - `python tools/build_pts_report_bundle.py`
4. Smoke QA (see skill `pts-hub-smoke-qa`)
5. Commit in a focused group

