# Ops Runbook

## Daily Checklist

1. Review telemetry triage summary (P0/P1/P2 counts).
2. Verify release artifact checksums.
3. Confirm no unresolved high-risk security findings.

## Incident Triage

- P0: immediate mitigation window (same day).
- P1: patch planning in current iteration.
- P2: backlog prioritization review.

## Clean-Machine Validation

- Validate install directory and executable presence.
- Validate uninstall entry exists.
- Record pass rate and environment matrix results.

## Release Operations

- Generate packaging manifest.
- Publish release note and publish record.
- Archive evidence artifacts.
