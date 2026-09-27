# SDD ledger — plan: docs/superpowers/plans/2026-09-26-toptenug-phase2-live-data.md

Executor: Native / superpowers:executing-plans
Branch: `feat/phase2-live-data`

## Setup rulings

- Ruling: local git worktree unavailable because this sandbox cannot resolve `github.com`; use the already-isolated GitHub branch as the workspace boundary and GitHub Actions as the executable RED/GREEN harness — cost if wrong: less convenient local iteration, but branch isolation and remote test evidence remain intact.
- Ruling: use a temporary branch-only `phase2-dev.yml` workflow with step-level `continue-on-error` during RED phases so expected failing tests do not generate repeated failed-workflow notifications; inspect the test step conclusion directly — cost if wrong: an inattentive reader could mistake overall workflow success for test success, so every task ledger entry must record the specific step conclusion.
- Ruling: legacy revision `0001_core_domain` imports live SQLAlchemy metadata. Rewriting historical migration 0001 mid-stream would be riskier than making Phase 2 migration `0002` idempotent against either an MVP-era or fresh schema. Phase 2 migration therefore checks existing tables/columns, leaves the new PostgreSQL enum value on downgrade, and retains the shared `vector` extension.

## Pre-flight shared-interface scan

- Tasks 1→9: `Settings` / database URL roles feed deployment validation. Spec and plan agree: runtime pooler URL separate from direct admin URL; production/staging fail fast.
- Tasks 2→3→5→7: `CandidateRecord` and `PROVISIONAL` persistence feed discovery, preview, and readiness. Interfaces are consistent; official readers must filter to `PUBLISHED`.
- Tasks 3→4: approved `Entity` + verified GitHub `SourceAccount` feed batch ingestion. No conflict.
- Tasks 4→6→7: observations and ingestion-run accounting feed Kampala-window derivation/readiness. No conflict.
- Tasks 5→8: preview API payload feeds web provisional rendering. No conflict; web must display API rank/order only.
- Tasks 6→10→14: quarter window/publish guard feeds E2E and official release. Exact Q3 exclusive boundary is `2026-09-30T21:00:00Z`.
- Tasks 9→10→11: deployment inputs/scripts feed deliberate deploy and staging provisioning. No conflict; Task 11 is external side-effect work after Stage A.

## Progress

- Task 1: RED confirmed in Actions run `36273756193`: 4 intended failures, 38 existing tests passed. Missing `Settings` fields/engine factories/readiness endpoint caused the failures.
- Task 1: complete — implementation through `e36101ff`; verification run `36273915623`: Ruff success, mypy success, pytest 42/42 pass. Safe `.env.example` files added; no secret values committed.
- Task 2: RED confirmed in Actions run `36273985199`: `CandidateRecord` import absent and `PROVISIONAL` schema contract missing. The same run also exposed a Task 1 mypy defect in environment parsing; systematic debugging traced it to `getenv()` returning `str` rather than the `Environment` Literal.
- Task 2: complete — typed environment parser fixed, `RankingRunStatus.PROVISIONAL`, `CandidateRecord`, ranking cutoff/count/validation metadata and migration `0002_phase2_live_data` added. Verification run `36274208114`: migration upgrade→downgrade→upgrade success, Ruff success, mypy success, pytest success.
- Task 3: first RED run `36274330349` failed on the intended missing `app.ingestion.candidates` module while migration/Ruff/mypy stayed green. Candidate persistence/review service added.
- Task 3: stricter identity-conflict RED run `36274439005` produced exactly 1 failed / 51 passed: same display name with two distinct GitHub identities was not yet review-gated. Minimal conflict detection added without merging identities.
- Task 3: CLI RED run `36274582995` produced exactly 2 failed / 52 passed: `discover --persist` and `review` command group were absent. Added persistent discovery count output plus `review list/approve/reject` commands.
- Task 3: complete — verification run `36274703565`: migration round-trip success, Ruff success, mypy success, full pytest success. Search/discovery ordering remains non-ranking data; candidate approval is the only path that creates an eligible entity.
- Task 4: service RED run `36274798408` failed at collection on the intended missing `ingest_github_batch` interface; migration/Ruff/mypy stayed green.
- Task 4: service implementation added durable `IngestionRun` creation before source calls, per-entity continuation/rollback, typed retry metadata, idempotent observation reuse, and preservation of prior observations.
- Task 4: CLI/static RED run `36274979645` produced exactly 2 failed / 57 passed for the absent `github-batch` operator surface, while review also found an unused import, exception narrowing issue, and `CandidateMetrics` dict invariance issue. All four were corrected.
- Task 4: complete — `toptenug ingest github-batch --limit N` selects reviewed eligible GitHub entities; `--entity-file` supports explicit controlled batches. Verification run `36275177892` on head `e6c5f308`: migration round-trip success, Ruff success, mypy success, full pytest success.
- Task 5: RED progression established provisional isolation first (`816639d`, `a15322d`) and then persistence/API implementation (`478b89b`, `cc61423`, `4b0bf39`). Final CLI RED was pinned at `61a9ccf`: `toptenug preview` was absent.
- Task 5: complete — commit `8d7aff76` adds the preview operator command using `create_provisional_run`; output includes run ID, reviewed pool size, ranked count, cutoff, algorithm version, and `official=false`. Verification run `36296873450`: migration round-trip success, Ruff success, mypy success, full core pytest success. Official endpoints/share metadata remain isolated from `PROVISIONAL` runs.
- Task 6: RED confirmed in run `36296975030`; migration/Ruff/mypy passed while pytest failed at collection because `app.quarterly.window` did not exist.
- Task 6: complete — `QuarterWindow` now derives quarter boundaries in `Africa/Kampala`, making Q3's exclusive cutoff `2026-09-30T21:00:00Z`; derive excludes exact-cutoff Q4 observations, late verification preserves both source `observed_at` and later `retrieved_at`, and official publish is blocked before quarter close via an injected-aware clock. Verification run `36297114840`: migration round-trip success, Ruff success, mypy success, full core pytest success. Test-only readability cleanup `da5f5867` keeps the same literal boundary semantics.

Status: Task 7 next.
