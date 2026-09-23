# TopTenUG Quarterly Operations Runbook

TopTenUG continuously collects evidence, but an official ranking changes only through an explicit quarterly publication run.

## Runtime boundaries

- `core`: FastAPI read service on Cloud Run.
- `worker`: Cloud Run Job image exposing the `toptenug` CLI.
- Cloud SQL PostgreSQL 16 + pgvector: canonical evidence, observation and ranking store.
- Cloud Scheduler: triggers jobs only. It contains no ranking formulas or weights.
- Secret Manager: `DATABASE_URL`, `GITHUB_TOKEN`, and Gemini/Google AI credentials.

## Job sequence

For a quarter such as `2026-Q3`, run these stages in order:

```bash
toptenug discover --universe technology
toptenug ingest github --entity <entity-uuid>
toptenug derive --quarter 2026-Q3
toptenug validate --category github-developers --quarter 2026-Q3
toptenug publish --category github-developers --quarter 2026-Q3
```

Discovery and ingestion may run repeatedly throughout the quarter. `publish` is a quarter-close operation and must run only after validation is green.

## Required secrets and permissions

- `DATABASE_URL`: Cloud SQL connection string; worker and API service accounts need Cloud SQL Client access.
- `GITHUB_TOKEN`: use the minimum read-only scopes needed for public GitHub API/GraphQL access. Do not grant repository write permissions.
- Gemini: configure either a Gemini API key or the Google Cloud/Vertex identity selected for the deployment. Gemini is permitted to discover, extract, classify and ground evidence only.

No secret may be committed to the repository or embedded in a Scheduler payload.

## Quarter-close checks

1. Freeze the source observation cutoff for the target quarter.
2. Verify Uganda eligibility decisions and unresolved review-required candidates.
3. Verify every official factor has provenance and the required minimum factor coverage.
4. Review stale critical sources, impossible values and anomaly flags.
5. Run DevRankUG deterministic replay against the frozen inputs.
6. Compare major movements against the previous published quarter.
7. Publish only after all blocking validation findings are cleared.
8. Smoke-test dashboard, leaderboard, profile, methodology and share-card metadata endpoints.

## Failure and rollback behavior

A failed validation or failed publication attempt must be recorded as `FAILED` and must not replace the prior `PUBLISHED` run. TopTenUG never edits the previous official ranks in-place. Correct the underlying evidence/observations or methodology, re-run validation, and create a new publication attempt.

If a factual correction affects a published quarter, retain the audit trail and recompute from corrected inputs. Do not manually patch a `RankingResult.rank` value.

## Methodology changes

Weights, normalizers, eligibility rules, missing-data behavior, tie breaking, anomaly policy or factor definitions are methodology. Change them in a new versioned TopTenUG algorithm specification and document the change before publication. Search ranking, Gemini confidence and Gemini result order are never official ranking factors.
