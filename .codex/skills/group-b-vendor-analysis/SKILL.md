---
name: group-b-vendor-analysis
description: Extract and normalize Logic/Structure findings for Group B from official Nordic/TI/Zephyr sources, add source catalog entries when needed, and encode results into Group_B_data structured blocks with traceability and confidence.
---

# Group B Vendor Analysis

Use this skill when doing deep analysis for `BPS`, `WSS`, `SCPS` from vendor sources.

## Source policy (strict)

- Logic: Nordic / nRF Connect SDK official sources (plus local Zephyr official repo code when used as pattern)
- Structure: TI SimpleLink official sources (plus approved local/official patterns)
- All external sources must exist in:
  - `tools/data/group_b_sdk_sources.json`
  - or `tools/data/group_b_official_sources.json`

## Work output model

Every new insight should usually produce:
1. `groupb_finding`
2. One or more `evidence_refs` (inside finding)
3. `groupb_source_observation` (source-by-source explanation of what/how)

## Confidence guidance

- `confirmed`: direct evidence in source
- `inferred`: design conclusion derived from multiple sources/patterns
- `needs_validation`: hypothesis not ready for implementation decisions

## When to add source catalog entries

Add/refresh source IDs if:
- you need a new official URL
- you need a new GitHub permalink for line-level traceability
- an existing URL changed version/page

## Preferred sequence per profile

1. Re-read current Logic/Structure docs
2. Identify weakest findings (low evidence / medium confidence)
3. Gather official source evidence
4. Add/update structured blocks
5. Run `python tools/check_group_b_hub.py`
6. Rebuild + smoke QA

## GitHub MCP usage

Use GitHub MCP when you need exact permalinks/line references from official repos.
Do not use non-official repos/blogs for normative findings.

