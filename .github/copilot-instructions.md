---
applyTo: '**'
---

# Zephyr BLE GATT Profile Builder System

This workspace contains a **pre-loaded knowledge system** for generating production-ready Bluetooth Low Energy GATT profiles for Zephyr RTOS.

## Mandatory Workspace Rule: CHANGELOG Updates

For any task that modifies tracked repository files, update `CHANGELOG/` immediately in the same task.

- Use group folders defined in `CHANGELOG/README.md` (`dashboard`, `docs`, `tools`, `firmware`, `infra`).
- Create or update an entry file named `YYYY-MM-DD-short-topic.md` under the relevant group folder.
- Keep entry structure aligned with `CHANGELOG/ENTRY_TEMPLATE.md`.
- Update `CHANGELOG/INDEX.md` together with the entry.
- If no commit was created yet, set `Commit: pending (no commit in this task)` and replace it later when commit hash exists.

`AGENTS.md` in repository root is the source of truth for the full changelog policy.

## Core System Files

- **`.github/data/profiles-db.yaml`** — Single source of truth: 24 validated BLE profiles with complete metadata, UUIDs, control point patterns, and implementation guidelines
- **`.github/data/profile-patterns.md`** — §10.0 Implementation patterns: 7 sections covering Notify, Indicate, RACP, SC CP, and state management architectures
- **`.github/instructions/zephyr-bt-profile-builder.instructions.md`** — Classification rules, output format, quality checklist
- **`.github/prompts/zephyr-bt-profile-builder.prompt.md`** — 5-step agent workflow: IDENTIFY → CLASSIFY → RESEARCH → BUILD → EXPLAIN

## System Purpose

Generate Zephyr-native BLE profile implementations by:
1. Identifying which of 24 validated profiles matches user requirements
2. Classifying profile complexity and control point patterns
3. Researching from profiles-db.yaml and pattern-patterns.md sources
4. Building Zephyr code from pattern templates (§10.0–§10.7)
5. Explaining payload structures and mandatory/optional characteristics

## To Use This System

Open `.github/prompts/zephyr-bt-profile-builder.prompt.md` as a **Copilot Custom Agent** or **Mode** in GitHub Copilot Chat. The system will:
- Auto-load profiles-db.yaml as context
- Apply profile-patterns.md §10.0–§10.7 logic
- Generate optimized Zephyr code matching your BLE requirements
- Validate outputs against Phase 1 quality checklist

## Key Documentation

- **System Journal:** `.github/docs/system-journal.md` — Complete history, design decisions, bug inventory, Phase 1 completion details
- **Source Governance:** `.github/data/sources-map.yaml` — Authority chain (Zephyr → TI → Auto-PTS → BT Spec → Nordic)
- **Profile Categories:** Health (HRS, HTS, BCS, GLS, CGMS, PLXS), Sport (RSCS, CSCS), Device (DIS, BAS), User (UDS), Alert (ANS, PASS, IAS, LLS), HID, Data Transfer (OTS), Location (IPS), and Generic services

For detailed setup or troubleshooting, see `.github/docs/system-journal.md` § "Activation Infrastructure" or the instructions file.
