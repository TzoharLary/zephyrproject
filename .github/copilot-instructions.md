---
applyTo: '**'
---

# Zephyr BLE GATT Profile Builder System

This workspace contains a **pre-loaded knowledge system** for generating production-ready Bluetooth Low Energy GATT profiles for Zephyr RTOS.

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
