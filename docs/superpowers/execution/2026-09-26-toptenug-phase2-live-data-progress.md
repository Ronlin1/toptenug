# SDD ledger — plan: docs/superpowers/plans/2026-09-26-toptenug-phase2-live-data.md

Executor: Native / superpowers:executing-plans
Branch: `feat/phase2-live-data`

## Setup rulings

- Ruling: local git worktree unavailable because this sandbox cannot resolve `github.com`; use the already-isolated GitHub branch as the workspace boundary and GitHub Actions as the executable RED/GREEN harness — cost if wrong: less convenient local iteration, but branch isolation and remote test evidence remain intact.
- Ruling: use a temporary branch-only `phase2-dev.yml` workflow with step-level `continue-on-error` during RED phases so expected failing tests do not generate repeated failed-workflow notifications; inspect the test step conclusion directly — cost if wrong: an inattentive reader could mistake overall workflow success for test success, so every task ledger entry must record the specific step conclusion.

## Pre-flight shared-interface scan

- Tasks 1→9: `Settings` / database URL roles feed deployment validation. Spec and plan agree: runtime pooler URL separate from direct admin URL; production/staging fail fast.
- Tasks 2→3→5→7: `CandidateRecord` and `PROVISIONAL` persistence feed discovery, preview, and readiness. Interfaces are consistent; official readers must filter to `PUBLISHED`.
- Tasks 3→4: approved `Entity` + verified GitHub `SourceAccount` feed batch ingestion. No conflict.
- Tasks 4→6→7: observations and ingestion-run accounting feed Kampala-window derivation/readiness. No conflict.
- Tasks 5→8: preview API payload feeds web provisional rendering. No conflict; web must display API rank/order only.
- Tasks 6→10→14: quarter window/publish guard feeds E2E and official release. Exact Q3 exclusive boundary is `2026-09-30T21:00:00Z`.
- Tasks 9→10→11: deployment inputs/scripts feed deliberate deploy and staging provisioning. No conflict; Task 11 is external side-effect work after Stage A.

Status: setup complete; Task 1 next.
