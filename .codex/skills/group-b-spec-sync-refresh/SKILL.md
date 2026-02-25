---
name: group-b-spec-sync-refresh
description: Refresh Bluetooth SIG specification artifacts for Group B profiles (BPS/WSS/SCPS), update the local sync manifest, and validate consistency with docs/profiles and the Hub spec inventory.
---

# Group B Spec Sync Refresh

Use this skill when refreshing official Bluetooth SIG artifacts for:
- `BPS`
- `WSS`
- `SCPS`

## Scope

This skill manages only spec/document synchronization and manifest consistency.

## Source policy

Use only official SIG/PTS/Qualification/Support sources.

## Workflow

1. Use the global skill `bluetooth-profile-doc-sync` to sync profile artifacts into `docs/Profiles` (or the project's active path if already normalized to lowercase).
2. Ensure artifacts are present under:
- `docs/profiles/BPS` or `docs/Profiles/BPS`
- `docs/profiles/WSS` or `docs/Profiles/WSS`
- `docs/profiles/SCPS` or `docs/Profiles/SCPS`
3. Update:
- `tools/data/group_b_spec_sync_manifest.json`
4. Validate:
- `python tools/check_group_b_hub.py --allow-threshold-fail`
5. Rebuild:
- `python tools/build_pts_report_bundle.py`

## Consistency checklist

- `spec_page_url` matches adopted/latest target used for sync
- `resolved_title` matches synced profile version
- `status` is `synced` (or a clear partial/failure status with notes)
- `notes` explain locked/member-only cases

