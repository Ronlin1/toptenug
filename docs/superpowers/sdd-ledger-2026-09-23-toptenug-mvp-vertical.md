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
- Restored and ported the complete backend API/domain/ingestion/intelligence/quarterly/ranking/source/E2E verification suites to the current production interfaces.
- Fixed Vitest/Playwright suite separation so unit tests do not collect E2E specs.
- Fixed frontend/backend runtime contracts for dashboard, leaderboard, profiles/history, methodology, and canonical share metadata.
- Fixed CI commands to execute from their project roots.
- Fixed Gemini, GitHub-adapter and derived-metric typing boundaries instead of weakening static checks.
- Added PyYAML type stubs so mypy remains active.
- Added deterministic direct `METRIC` and `TREND` ranking entry points alongside the versioned `INDEX` engine.
- Corrected GitHub 90-day activity semantics, explicit UTC query windows, provenance, fork filtering, and retryable rate-limit behavior.
- Remediated the GitGuardian local-development database password finding from historical commit `f81487f`; active feature configuration contains no hard-coded database password.

## Release-gate evidence

GitHub Actions run `36229704779` (run #134), head `74a7a533bd7b63ab130f3178662cb3876aeb7444`:

### Core

- dependency sync: PASS
- Alembic upgrade → downgrade → upgrade: PASS
- Ruff: PASS
- mypy: PASS (`38` source files)
- pytest: PASS (`38 passed`; one upstream Starlette/httpx deprecation warning)

### Web

- pnpm install: PASS
- TypeScript lint/typecheck: PASS
- Vitest: PASS
- Playwright browser install: PASS
- Playwright desktop/mobile tests: PASS

## Final whole-branch review

- `main` remains unchanged at base `62170377080cc92e84a554ed7d12088a78cfab45`.
- Ranking engine imports only TopTenUG domain/ranking modules and has no Google/Gemini/search dependency.
- Gemini/Google remains an evidence/discovery support boundary and cannot emit official score/rank fields.
- Public leaderboard limits remain exactly `10`, `20`, `30`, and `50`.
- Share metadata is resolved from immutable published `rankingResultId`; arbitrary client rank/score query values cannot replace official values.
- Failed validation keeps the previous official snapshot intact.
- Full E2E fixture proves discovery-order independence and source → evidence → eligibility → metrics → TopTenUG algorithm → publish → public API/profile/history/share flow.
- Active development/CI configuration contains no hard-coded database password.
- No merge has been performed.

## Integration status

Implementation and release gates are complete on the feature branch. The branch remains unmerged pending the human integration decision.
