# SDD ledger — plan: docs/superpowers/plans/2026-09-26-toptenug-phase2-live-data.md

Executor: Native / superpowers:executing-plans
Branch: `feat/phase2-live-data`

## Setup rulings

- Ruling: local git worktree unavailable because this sandbox cannot resolve `github.com`; use the already-isolated GitHub branch as the workspace boundary and GitHub Actions as the executable RED/GREEN harness — cost if wrong: less convenient local iteration, but branch isolation and remote test evidence remain intact.
- Ruling: use a temporary branch-only `phase2-dev.yml` workflow with step-level `continue-on-error` during RED phases so expected failing tests do not generate repeated failed-workflow notifications; inspect the test step conclusion directly — cost if wrong: an inattentive reader could mistake overall workflow success for test success, so every task ledger entry must record the specific step conclusion.
- Ruling: legacy revision `0001_core_domain` imports live SQLAlchemy metadata. Rewriting historical migration 0001 mid-stream would be riskier than making Phase 2 migration `0002` idempotent against either an MVP-era or fresh schema. Phase 2 migration therefore checks existing tables/columns, leaves the new PostgreSQL enum value on downgrade, and retains the shared `vector` extension.
- Ruling: Task 7 uses `services/core/app/readiness.py` instead of the plan's `app/operations/readiness.py` because `app/operations.py` is already a module; converting it into a package would be unrelated refactoring. The planned interface and behavior are unchanged.

## Pre-flight shared-interface scan

- Tasks 1→9: `Settings` / database URL roles feed deployment validation. Spec and plan agree: runtime pooler URL separate from direct admin URL; production/staging fail fast.
- Tasks 2→3→5→7: `CandidateRecord` and `PROVISIONAL` persistence feed discovery, preview, and readiness. Interfaces are consistent; official readers must filter to `PUBLISHED`.
- Tasks 3→4: approved `Entity` + verified GitHub `SourceAccount` feed batch ingestion. No conflict.
- Tasks 4→6→7: observations and ingestion-run accounting feed Kampala-window derivation/readiness. No conflict.
- Tasks 5→8: preview API payload feeds web provisional rendering. No conflict; web must display API rank/order only.
- Tasks 6→10→14: quarter window/publish guard feeds E2E and official release. Exact Q3 exclusive boundary is `2026-09-30T21:00:00Z`.
- Tasks 9→10→11: deployment inputs/scripts feed deliberate deploy and staging provisioning. No conflict; Task 11 is external side-effect work after Stage A.

## Progress

- Task 1: complete — verification run `36273915623`: migrations/Ruff/mypy/pytest green.
- Task 2: complete — verification run `36274208114`: schema/provisional/candidate migration green.
- Task 3: complete — verification run `36274703565`: persistent grounded discovery/review green.
- Task 4: complete — verification run `36275177892`: batch GitHub ingestion/idempotency/failure continuation green.
- Task 5: complete — verification run `36296873450`: provisional persistence/API/CLI green; official surfaces exclude provisional.
- Task 6: complete — verification run `36297114840`: Kampala quarter window/freeze guard green; Q3 exclusive cutoff `2026-09-30T21:00:00Z`.
- Task 7: complete — exact CLI head run `36297498445`: launch-readiness policy + human review procedure green. A later Task 9 RED run exposed an over-generic mypy annotation in `_count`; fixed without weakening mypy at commit `acb13fe1`.
- Task 8: complete — exact-head run `36297945459`: TypeScript, Vitest and Playwright green. Preview is explicit/non-official, API-ranked, 10/20/30/50 only, and official sharing is suppressed.
- Task 9: RED confirmed in run `36298053802`: pytest collection failed because `app.deployment_config` did not exist; the same raw run exposed the Task 7 mypy annotation issue noted above. Implemented `app/deployment_config.py`, secret-safe CLI validator, Supabase/Vercel/GCP/runbook documentation, safe env-name template, strict Frankfurt region pair, runtime-pooler/direct-admin separation, preview/production routing checks, and removed secret-shaped fixture strings. Exact-head run `36298264404` is fully green: migrations, Ruff, mypy, full core pytest, TypeScript, Vitest, Playwright, deployment config validation, core Docker build and worker Docker build all pass.

Status: Task 10 next.
