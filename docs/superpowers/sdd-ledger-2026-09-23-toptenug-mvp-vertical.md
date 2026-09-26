# TopTenUG MVP Vertical SDD Ledger

Plan: `docs/superpowers/plans/2026-09-23-toptenug-mvp-vertical.md`

Branch: `feat/toptenug-mvp-vertical`

Base: `62170377080cc92e84a554ed7d12088a78cfab45`

## Execution invariant

Google/Gemini, search systems, source APIs, journals, public datasets, and public-web extraction provide evidence and metric inputs only. Official TopTenUG ranks are produced solely by deterministic, versioned TopTenUG ranking code/config.

## Execution note

This ChatGPT harness did not expose a native subagent-dispatch primitive. The approved subagent-driven workflow was therefore preserved as task-by-task implementation and separate review/verification gates in the same session rather than falsely representing ordinary tool calls as independent subagents.

## Task ledger

| Task | Implementation | Review / verification | Status |
| --- | --- | --- | --- |
| 1. Bootstrap monorepo and health checks | FastAPI core, Next.js workspace, PostgreSQL/pgvector and CI scaffold | Health contract and executable CI bootstrap verified | Complete |
| 2. Evidence-first domain/database | Entity, evidence, observation, metric, algorithm, run and result contracts plus Alembic migration | Migration and provenance constraints reviewed | Complete |
| 3. Deterministic ranking engine | METRIC/INDEX/TREND engine and `DevRankUG 1.0.0` | Deterministic replay, stable tie break, missing-data policy and AI-isolation reviewed | Complete |
| 4. GitHub hard-metric source | GitHub profile/repository/contribution collection with provenance and rate-limit handling | Source adapter emits observations only, never score/rank | Complete |
| 5. Google/Gemini intelligence support | Grounded discovery/evidence extraction contract | Grounding required; ambiguous Uganda relation goes to review; no official ranking output | Complete |
| 6. Ingestion/entity/eligibility | Evidence persistence, entity resolution and Uganda eligibility gates | Conflicting/insufficient Uganda evidence cannot enter official ranking | Complete |
| 7. Quarterly publication | Validation, anomaly gates, immutable ranking runs/results | Failed validation preserves previous official snapshot; retry path supported | Complete |
| 8. Public read API | Rankings, entity/profile, dashboard, methodology and SQL-backed reads | Only official published results exposed; public limits restricted to 10/20/30/50 | Complete |
| 9. Discovery UI/leaderboard | Homepage, Technology universe and GitHub Developers leaderboard | Browser displays API-computed official ranks; responsive list expansion verified | Complete |
| 10. Profiles/methodology/analytics | Profiles, rank history, factor breakdown and methodology views | Algorithm version, weights, confidence and evidence surfaced | Complete |
| 11. Official share cards | Canonical result-ID share metadata and social card UI/routes | Client rank/score cannot override immutable published result metadata | Complete |
| 12. CLI/operations/E2E/CI | discover/ingest/derive/validate/publish workflow, containers/runbook and end-to-end gates | Historical cutoff, anomaly checks, publication path and public-read integration reviewed | Complete |

## Recovery and debugging record

- Recovered the implementation after a sandbox runtime reset without modifying `main`.
- Restored the complete `apps/web` workspace from the verified implementation branch after an incomplete GitHub subtree push.
- Fixed Vitest/Playwright suite separation so unit tests do not collect E2E specs.
- Fixed CI commands to execute from their project roots.
- Fixed Gemini, GitHub-adapter and derived-metric typing boundaries instead of weakening static checks.
- Added PyYAML type stubs so mypy remains active.
- Remediated the GitGuardian local-development database password finding from historical commit `f81487f`; active feature configuration contains no hard-coded database password.

## Release-gate evidence

GitHub Actions run `36228762469` (run #112), head `870d832d54cb232a4f40b15a0bd43e0c581fb88c`:

### Core

- dependency sync: PASS
- Alembic upgrade: PASS
- Ruff: PASS
- mypy: PASS
- pytest: PASS

### Web

- pnpm install: PASS
- TypeScript lint/typecheck: PASS
- Vitest: PASS
- Playwright browser install: PASS
- Playwright desktop/mobile tests: PASS

## Final review gates still required after this ledger commit

- CI must pass again on the exact final branch head.
- Confirm `main` remains unchanged from base.
- Confirm ranking package contains no Google/Gemini/search dependency.
- Confirm public leaderboard limits remain exactly 10/20/30/50.
- Confirm share-card rank and score derive from immutable published result IDs.
- Confirm no merge is performed until all final gates are green.
