# TopTenUG Phase 2 — Live Data & Public Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the verified TopTenUG GitHub Developers MVP into a production-deployable, real-data system that can discover and review Uganda-linked developers, publish clearly separated provisional rankings before quarter close, and publish an immutable official 2026-Q3 snapshot only after the Kampala cutoff and launch gates pass.

**Architecture:** Keep the existing Next.js → FastAPI → PostgreSQL boundary and TopTenUG-owned ranking engine. Deploy Next.js on Vercel, FastAPI/worker containers on Cloud Run, and canonical PostgreSQL/pgvector on Supabase. External intelligence/source systems only produce candidates, evidence and metrics; `app/ranking/**` remains the only official rank computation path.

**Tech Stack:** Python 3.13+, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, Psycopg 3, pgvector, Google GenAI, Typer, pytest/Ruff/mypy; Next.js 15, React 19, TypeScript 5.7, Vitest, Playwright; Supabase PostgreSQL; Vercel; Google Cloud Run, Cloud Run Jobs, Cloud Scheduler and Secret Manager.

**Spec:** `docs/superpowers/specs/2026-09-26-toptenug-phase2-live-data-design.md`

## Global Constraints

- **Ranking ownership:** Google/Gemini, search, GitHub, public web and datasets provide evidence or metrics only. They never provide official score/rank fields.
- **Ranking isolation:** `services/core/app/ranking/**` must not import `google.genai`, Gemini/search clients or discovery ordering.
- **Official category:** first production vertical remains **Technology → GitHub Developers → Uganda**.
- **Eligibility:** official `Ugandan GitHub Developers` includes `UGANDAN_IN_UGANDA` and `UGANDAN_DIASPORA`; `UGANDA_BASED_NON_UGANDAN` is excluded.
- **Launch pool:** first national release requires at least **100 discovered plausible candidates** and at least **50 approved, category-eligible candidates**.
- **Public sizes:** only 10, 20, 30 and 50; default is 10.
- **Run states:** `PROVISIONAL` and `PUBLISHED` are structurally distinct. Official endpoints/share cards never treat provisional data as official.
- **Q3 cutoff:** `2026-09-30 23:59:59 Africa/Kampala`, equivalent to an exclusive UTC boundary of `2026-09-30T21:00:00Z`.
- **Official freeze:** no 2026-Q3 official publication before the cutoff.
- **Immutability:** a failed validation/publication leaves the prior official snapshot unchanged.
- **Secrets:** no usable production/staging credential may be committed to Git, test fixtures or examples.
- **CI noise:** full code CI runs on PRs to `main`, pushes to `main`, or manual dispatch; feature-branch pushes do not run the full suite automatically; docs-only changes skip code CI; superseded runs cancel.
- **Deployment split:** Vercel serves web only; Cloud Run serves FastAPI; Cloud Run Jobs run operations; Vercel never receives database/service-role credentials.
- **Database regions:** first deployment pair is Supabase `eu-central-1` (Frankfurt) and Cloud Run `europe-west3` (Frankfurt). If either region is unavailable at provisioning time, stop and record a region-change decision rather than silently moving only one side.
- **Database connectivity:** Cloud Run API uses the Supabase transaction pooler; Psycopg automatic prepared statements are disabled for that engine. Alembic/administrative migrations use `DATABASE_ADMIN_URL` through the direct connection.
- **Cloud Scheduler:** scheduler only invokes jobs; no ranking formulas or publication decisions live in scheduler config.
- **Production publish:** publication remains manually authorized after validation; it is never a blind scheduled action.

## Review Focus

1. **Provisional leakage:** an official endpoint or share route must never return a `PROVISIONAL` run; Task 5 pins this with API/share tests.
2. **Quarter-boundary/timezone drift:** observations after `2026-09-30T20:59:59Z` must not enter Q3; Task 6 pins Kampala/UTC boundary behavior.
3. **Duplicate candidate identity:** repeated discovery through different sources must not inflate the candidate count or create duplicate GitHub identities; Task 3 pins this.
4. **Partial source/rate-limit failure:** one GitHub failure must not zero metrics or abort unrelated entities, and the run must be auditable; Task 4 pins this.
5. **Environment misrouting:** preview web/API/database must never point at production unintentionally, and production migrations must never use the transaction pooler; Tasks 1 and 9 pin configuration validation.

---

# Stage A — Production platformization

### Task 1: Production configuration, database connection roles and diagnostics

**Files:**
- Modify: `services/core/app/config.py`
- Modify: `services/core/app/db.py`
- Modify: `services/core/app/main.py`
- Create: `services/core/tests/test_config.py`
- Modify: `services/core/tests/test_health.py`
- Create: `services/core/.env.example`
- Create: `apps/web/.env.example`

**Interfaces:**
- Consumes: current `get_settings()` and SQLAlchemy `SessionLocal`.
- Produces: `Settings.environment`, `Settings.database_url`, `Settings.database_admin_url`, `Settings.allowed_origins`, `Settings.commit_sha`, `Settings.provisional_public_enabled`; `create_runtime_engine(settings) -> Engine`; `/health` and `/ready` diagnostic payloads.

- [ ] **Step 1: Write failing configuration tests**

Pin these behaviors:

```python
def test_production_requires_database_and_public_origin(): ...
def test_runtime_engine_disables_psycopg_prepare_for_transaction_pooler(): ...
def test_admin_url_is_separate_from_runtime_pooler_url(): ...
def test_ready_reports_environment_and_commit_without_secret_values(): ...
```

Assertions must prove that production/staging fail fast when required URLs/origins are absent and diagnostics expose only environment, commit SHA, database reachability and app version.

- [ ] **Step 2: Run the focused tests**

Run: `cd services/core && uv run pytest tests/test_config.py tests/test_health.py -v`

Expected: FAIL because the new settings/readiness contracts do not exist.

- [ ] **Step 3: Implement environment-aware settings and engine factories**

In `config.py`, add exact environment names `local | staging | production`, `DATABASE_ADMIN_URL`, `TOPTENUG_ALLOWED_ORIGINS`, `TOPTENUG_COMMIT_SHA`, and `TOPTENUG_PROVISIONAL_PUBLIC_ENABLED`.

In `db.py`, provide:

```python
def create_runtime_engine(settings: Settings) -> Engine: ...
def create_admin_engine(settings: Settings) -> Engine: ...
```

For a Supabase transaction-pooler URL, pass Psycopg `prepare_threshold=None`; never apply that rule to the admin/direct engine implicitly.

- [ ] **Step 4: Add CORS/readiness wiring and safe env examples**

`main.py` must configure explicit origins for production. Staging may additionally use a documented Vercel preview-origin regex. `.env.example` files list names only and contain no usable credentials.

- [ ] **Step 5: Verify and commit**

Run:

```bash
cd services/core && uv run ruff check . && uv run mypy app && uv run pytest tests/test_config.py tests/test_health.py -q
```

Commit: `feat: add production configuration boundaries`

---

### Task 2: Persist Phase 2 run state and candidate staging schema

**Files:**
- Modify: `services/core/app/domain/enums.py`
- Modify: `services/core/app/domain/models.py`
- Create: `services/core/migrations/versions/0002_phase2_live_data.py`
- Create: `services/core/tests/domain/test_phase2_schema.py`

**Interfaces:**
- Consumes: existing `Entity`, `Evidence`, `RankingRun`, `IngestionRun`.
- Produces: `RankingRunStatus.PROVISIONAL`; `CandidateRecord`; ranking-run cutoff/count/validation metadata.

- [ ] **Step 1: Write the failing schema tests**

Require:

```python
assert RankingRunStatus.PROVISIONAL.value == "PROVISIONAL"
```

`CandidateRecord` must persist: `id`, normalized identity key, display name, GitHub login/profile when known, profile map, proposed Uganda relation, confidence, source URLs, discovery source, discovered timestamp, review status, resolved entity ID and reviewer note.

`RankingRun` must persist: `cutoff_at`, `candidate_count`, `validation_details` in addition to existing status/version relationships.

- [ ] **Step 2: Verify RED**

Run: `cd services/core && uv run pytest tests/domain/test_phase2_schema.py -v`

Expected: FAIL on missing enum/model fields.

- [ ] **Step 3: Implement model changes and Alembic migration**

Migration `0002_phase2_live_data` must:

- add `PROVISIONAL` to the persisted run-status representation safely;
- create `candidate_records` with uniqueness on normalized identity key;
- add ranking-run cutoff/count/validation columns;
- `CREATE EXTENSION IF NOT EXISTS vector` without adding semantic-search tables yet.

- [ ] **Step 4: Prove migration round-trip**

Run against ephemeral PostgreSQL:

```bash
cd services/core
uv run alembic upgrade head
uv run alembic downgrade 0001_core_domain
uv run alembic upgrade head
```

Expected: PASS and schema test PASS.

- [ ] **Step 5: Commit**

Commit: `feat: add live-data persistence model`

---

### Task 3: Persist grounded discovery and human review workflow

**Files:**
- Create: `services/core/app/ingestion/candidates.py`
- Modify: `services/core/app/intelligence/gemini.py`
- Modify: `services/core/app/cli.py`
- Create: `services/core/tests/ingestion/test_candidate_records.py`
- Modify: `services/core/tests/intelligence/test_gemini.py`

**Interfaces:**
- Consumes: `GeminiIntelligenceProvider.discover(query) -> list[CandidateProposal]`, `CandidateRecord`, `Evidence`, existing entity-resolution rules.
- Produces:

```python
def persist_candidate_proposals(session: Session, proposals: list[CandidateProposal], discovery_source: str) -> CandidatePersistSummary: ...
def list_review_queue(session: Session, status: ReviewStatus) -> list[CandidateRecord]: ...
def approve_candidate(session: Session, candidate_id: UUID, relation: UgandaRelation, reviewer_note: str) -> Entity: ...
def reject_candidate(session: Session, candidate_id: UUID, reviewer_note: str) -> CandidateRecord: ...
```

- [ ] **Step 1: Write failing persistence/idempotency tests**

Cover:

- same GitHub profile discovered twice creates one candidate;
- same person from two grounded URLs enriches the same candidate rather than increasing the count;
- conflicting GitHub identities with the same display name remain separate/review-required;
- Gemini output with no source URL is rejected;
- approval cannot use `UGANDA_BASED_NON_UGANDAN` for this category;
- approval links evidence and creates/resolves exactly one `Entity`/`SourceAccount`.

- [ ] **Step 2: Verify RED**

Run: `cd services/core && uv run pytest tests/ingestion/test_candidate_records.py tests/intelligence/test_gemini.py -v`

- [ ] **Step 3: Implement candidate repository/service**

Identity priority for `normalized_identity_key`:

1. normalized GitHub profile/login when available;
2. otherwise normalized first-party profile URL;
3. otherwise stable hash of normalized display name + sorted grounded source URLs.

Never use discovery list position in the identity key or ranking pipeline.

- [ ] **Step 4: Extend CLI review commands**

Add:

```text
toptenug discover --universe technology --persist
toptenug review list --status REVIEW_REQUIRED
toptenug review approve --candidate <uuid> --relation UGANDAN_IN_UGANDA --note "..."
toptenug review reject --candidate <uuid> --note "..."
```

`discover --persist` prints counts (`proposals`, `created`, `updated`, `review_required`) rather than raw ranking-like ordering.

- [ ] **Step 5: Verify and commit**

Run full ingestion/intelligence tests plus Ruff/mypy.

Commit: `feat: persist candidate discovery and review`

---

### Task 4: Batch GitHub ingestion with durable run accounting

**Files:**
- Modify: `services/core/app/operations.py`
- Modify: `services/core/app/cli.py`
- Create: `services/core/tests/ingestion/test_github_batch.py`
- Modify: `services/core/tests/sources/test_github.py`

**Interfaces:**
- Consumes: `ingest_github_entity(session, entity_id)` and approved entities with verified GitHub `SourceAccount`.
- Produces:

```python
async def ingest_github_batch(session: Session, entity_ids: list[UUID], *, continue_on_error: bool = True) -> BatchIngestionResult: ...
```

`BatchIngestionResult` contains attempted/succeeded/failed/observations-added counts plus typed per-entity failures.

- [ ] **Step 1: Write failing batch tests**

Prove:

- one 429/retryable source failure is recorded without zeroing old observations;
- unrelated entities continue when `continue_on_error=True`;
- rerunning the same observations does not inflate observation count;
- each batch creates/finishes one database `IngestionRun` with status/counts/failure details;
- no rank/score fields are created by source ingestion.

- [ ] **Step 2: Verify RED**

Run: `cd services/core && uv run pytest tests/ingestion/test_github_batch.py tests/sources/test_github.py -v`

- [ ] **Step 3: Implement durable batch orchestration**

Do not write operational truth only to `.toptenug/jobs.jsonl`. Database `IngestionRun` becomes the authoritative run record; local JSON may remain an optional developer mirror.

- [ ] **Step 4: Add CLI command**

Add:

```text
toptenug ingest github-batch --limit 25
toptenug ingest github-batch --entity-file <path>
```

Default selection is approved eligible entities with a verified GitHub account and no unresolved identity conflict.

- [ ] **Step 5: Verify and commit**

Commit: `feat: add auditable GitHub batch ingestion`

---

### Task 5: Add structurally separate provisional ranking persistence and API

**Files:**
- Modify: `services/core/app/operations.py`
- Create: `services/core/app/api/preview.py`
- Modify: `services/core/app/api/__init__.py`
- Modify: `services/core/app/api/sql_read.py`
- Modify: `services/core/app/api/rankings.py`
- Create: `services/core/tests/quarterly/test_provisional_runs.py`
- Create: `services/core/tests/api/test_preview_rankings.py`
- Modify: `services/core/tests/api/test_share_metadata.py`

**Interfaces:**
- Consumes: `evaluate_snapshot(...)`, `RankingRunStatus.PROVISIONAL`.
- Produces:

```python
def create_provisional_run(session: Session, slug: str, quarter: str, cutoff_at: datetime) -> RankingRun: ...
GET /v1/preview/rankings/{slug}?limit=10|20|30|50&quarter=YYYY-QN
```

- [ ] **Step 1: Write failing isolation tests**

Prove:

- provisional creation writes a new auditable run and never mutates a published run;
- `/v1/rankings/{slug}` ignores provisional rows;
- `/v1/preview/rankings/{slug}` returns only provisional rows and includes `official: false`, reviewed pool count and cutoff timestamp;
- share metadata rejects a provisional `RankingResult.id` with 404/409 rather than rendering an official card;
- public limit validation remains exactly 10/20/30/50.

- [ ] **Step 2: Verify RED**

Run focused quarterly/API tests.

- [ ] **Step 3: Implement provisional write/read path**

Official publication remains a separate run. Do not implement `PROVISIONAL -> PUBLISHED` as an in-place state mutation.

- [ ] **Step 4: Add CLI provisional command**

```text
toptenug preview --category github-developers --quarter 2026-Q3
```

The command prints run ID, pool size, ranked count, cutoff, algorithm version and `official=false`.

- [ ] **Step 5: Verify and commit**

Commit: `feat: add provisional ranking surface`

---

### Task 6: Make quarter windows Kampala-correct and freeze Q3 safely

**Files:**
- Create: `services/core/app/quarterly/window.py`
- Modify: `services/core/app/operations.py`
- Modify: `services/core/app/quarterly/validate.py`
- Create: `services/core/tests/quarterly/test_window.py`
- Modify: `services/core/tests/operations/test_quarter_cutoff.py` if present, otherwise create it.

**Interfaces:**
- Produces:

```python
@dataclass(frozen=True)
class QuarterWindow:
    quarter: str
    timezone: str
    starts_at: datetime
    ends_at_exclusive: datetime

def quarter_window(quarter: str, timezone: str = "Africa/Kampala") -> QuarterWindow: ...
def assert_publish_window_open(quarter: str, now: datetime) -> None: ...
```

- [ ] **Step 1: Write exact cutoff tests**

For `2026-Q3` assert:

```python
window.ends_at_exclusive.isoformat() == "2026-09-30T21:00:00+00:00"
```

Also prove:

- `2026-09-30T20:59:59Z` is eligible;
- `2026-09-30T21:00:00Z` is excluded;
- `publish_quarter(..., 2026-Q3)` rejects a clock before the cutoff;
- deriving Q3 never selects a newer Q4 observation;
- late verification is auditable and cannot silently move an observation timestamp backward.

- [ ] **Step 2: Verify RED**

- [ ] **Step 3: Replace UTC-calendar boundary logic with `QuarterWindow`**

All derive/validate/publish code must use the shared utility, not ad-hoc datetime arithmetic.

- [ ] **Step 4: Verify and commit**

Commit: `fix: enforce Kampala quarter cutoffs`

---

### Task 7: Add launch-readiness policy and operator report

**Files:**
- Create: `services/core/app/operations/readiness.py`
- Modify: `services/core/app/cli.py`
- Create: `services/core/tests/operations/test_launch_readiness.py`
- Create: `docs/operations/live-data-review.md`

**Interfaces:**
- Produces:

```python
@dataclass(frozen=True)
class LaunchReadinessReport:
    discovered: int
    reviewed: int
    eligible: int
    github_resolved: int
    qualified: int
    unresolved_duplicates: int
    blocking_anomalies: int
    source_failures: int
    ready_for_national_release: bool

def launch_readiness(session: Session, category: str, quarter: str) -> LaunchReadinessReport: ...
```

- [ ] **Step 1: Write launch-gate tests**

`ready_for_national_release` is false unless all are true:

- discovered >= 100;
- eligible >= 50;
- at least 50 category-qualified rows exist for the Top 50;
- zero unresolved duplicate conflicts;
- zero blocking anomalies;
- ranking validation passes.

A smaller pool may still be `preview_ready=True` if it has reviewed eligible candidates and a valid provisional run.

- [ ] **Step 2: Verify RED**

- [ ] **Step 3: Implement report + CLI**

Add:

```text
toptenug report launch-readiness --category github-developers --quarter 2026-Q3
```

Output must include counts and blockers; it must never auto-approve/reject a person.

- [ ] **Step 4: Document human review procedure and commit**

Commit: `feat: add live-data launch readiness gates`

---

### Task 8: Render provisional preview explicitly in the public web app

**Files:**
- Modify: `apps/web/lib/api.ts`
- Create: `apps/web/components/provisional-banner.tsx`
- Modify: `apps/web/app/technology/github-developers/page.tsx`
- Modify: `apps/web/app/page.tsx`
- Create: `apps/web/tests/provisional-ranking.test.tsx`
- Modify: `apps/web/e2e/responsive.spec.ts`

**Interfaces:**
- Consumes: official `/v1/rankings/*` and preview `/v1/preview/rankings/*` payloads.
- Produces: explicit preview mode selected by API availability/config, never inferred from missing official data.

- [ ] **Step 1: Write UI tests**

Prove:

- provisional page says **“Provisional — not an official quarterly ranking”**;
- reviewed/eligible pool size is visible;
- official share action is absent/disabled for provisional rows;
- official published page has no provisional badge;
- 10/20/30/50 controls remain the only options;
- empty preview state explains that discovery/review is in progress.

- [ ] **Step 2: Verify RED**

Run: `pnpm --dir apps/web test`

- [ ] **Step 3: Implement preview rendering without client-side ranking**

The web app must display the API-provided rank/order only.

- [ ] **Step 4: Run browser tests at desktop/mobile and commit**

Run:

```bash
pnpm --dir apps/web lint
pnpm --dir apps/web test
pnpm --dir apps/web exec playwright test
```

Commit: `feat: add provisional live-data preview UI`

---

### Task 9: Prepare reproducible Supabase, Cloud Run and Vercel deployment configuration

**Files:**
- Modify: `infra/cloudrun/core.Dockerfile`
- Modify: `infra/cloudrun/worker.Dockerfile`
- Create: `infra/gcp/env.example`
- Create: `infra/gcp/deploy-service.sh`
- Create: `infra/gcp/deploy-jobs.sh`
- Create: `infra/gcp/configure-schedules.sh`
- Create: `infra/supabase/README.md`
- Create: `infra/vercel/README.md`
- Create: `docs/operations/deployment.md`
- Create: `scripts/validate_deployment_config.py`
- Create: `services/core/tests/operations/test_deployment_config.py`

**Interfaces:**
- Required deployment inputs are named variables, not committed values: `TOPTENUG_GCP_PROJECT_ID`, `TOPTENUG_GCP_REGION=europe-west3`, `TOPTENUG_ARTIFACT_REPOSITORY`, `DATABASE_URL`, `DATABASE_ADMIN_URL`, `GITHUB_TOKEN`, `GEMINI_API_KEY`, `TOPTENUG_PUBLIC_BASE_URL`, `TOPTENUG_ALLOWED_ORIGINS`, `TOPTENUG_COMMIT_SHA`, `NEXT_PUBLIC_API_BASE_URL`.

- [ ] **Step 1: Write deployment-config validation tests**

Prove:

- production refuses identical preview/production API URLs when explicitly marked different environments;
- production refuses missing admin URL for migrations;
- transaction-pooler runtime URL and direct admin URL are distinguishable;
- no secret values appear in generated shell command output/loggable config;
- region pair defaults to Supabase `eu-central-1` + Cloud Run `europe-west3`.

- [ ] **Step 2: Implement deployment scripts/docs**

Cloud Run names:

```text
toptenug-core
toptenug-discover-technology
toptenug-ingest-github
toptenug-derive-quarter
toptenug-validate-quarter
toptenug-publish-quarter
```

Scheduler creates only recurring discovery/ingestion/preview-derive triggers. Do **not** create an automatic production-publish schedule.

Use a dedicated scheduler invoker identity; worker/service identities receive only the secrets they need.

- [ ] **Step 3: Pin current platform-specific connection behavior**

Document that Supabase transaction mode uses port 6543/shared transaction pooler and does not support prepared statements; copy actual pooler host/username from the Supabase Connect output during provisioning rather than constructing them from region. Migrations use the direct connection returned by Supabase.

Vercel project root is `apps/web`; `NEXT_PUBLIC_API_BASE_URL` is scoped separately for Preview and Production.

- [ ] **Step 4: Verify Docker builds and config validator**

Run both container builds plus `python scripts/validate_deployment_config.py --environment staging` with fixture environment values.

- [ ] **Step 5: Commit**

Commit: `ops: add reproducible hybrid deployment configuration`

---

### Task 10: Separate test CI from deliberate deployment and add production smoke checks

**Files:**
- Modify: `.github/workflows/ci.yml`
- Create: `.github/workflows/deploy.yml`
- Create: `scripts/smoke_phase2.py`
- Create: `services/core/tests/e2e/test_phase2_live_flow.py`
- Create: `docs/operations/release-checklist.md`

**Interfaces:**
- Test CI remains PR/main/manual only.
- `deploy.yml` accepts `environment=staging|production`; production deploy is allowed only from `main` and remains manually dispatched initially.

- [ ] **Step 1: Write the complete fixture E2E test**

Execute:

```text
grounded candidate proposals
→ persisted candidate queue
→ explicit review/approval
→ batch GitHub observations
→ Kampala-window derivation
→ provisional DevRankUG run
→ preview API
→ official-publish attempt before cutoff rejected
→ fixture clock after cutoff
→ validation/readiness
→ immutable PUBLISHED run
→ official API/profile/share metadata
```

Assertions include zero dependence on discovery order and zero provisional leakage to official endpoints.

- [ ] **Step 2: Verify RED**

Run: `cd services/core && uv run pytest tests/e2e/test_phase2_live_flow.py -v`

- [ ] **Step 3: Implement smoke script**

`smoke_phase2.py` accepts `--api-base-url` and optional `--expect-preview`. It verifies `/health`, `/ready`, official/preview separation, allowed limits and no secret-like values in diagnostics.

- [ ] **Step 4: Implement deployment workflow without restoring CI noise**

No feature-branch push trigger. Deployment workflow never prints secret values. Production requires a `main` SHA and explicit `workflow_dispatch` environment selection.

- [ ] **Step 5: Run the full release suite and commit**

```bash
cd services/core && uv run ruff check .
cd services/core && uv run mypy app
cd services/core && uv run pytest -q
pnpm --dir apps/web lint
pnpm --dir apps/web test
pnpm --dir apps/web exec playwright test
```

Commit: `feat: complete Phase 2 production platformization`

---

# Stage B — 2026-Q3 live-data launch campaign

### Task 11: Provision staging infrastructure and prove production-equivalent connectivity

**Files:**
- Update after verification: `docs/operations/deployment.md`
- Create: `docs/operations/deployment-records/staging.md`

**Interfaces:**
- Uses the connected Supabase and Vercel integrations where available; Cloud Run is deployed through the checked-in scripts/GitHub deployment path using operator-supplied Google Cloud project/IAM values.
- Produces staging URLs/project references recorded without secrets.

- [ ] **Step 1: Create Supabase staging project**

Name: `toptenug-staging`.

Region: `eu-central-1`.

Enable `vector`; run Alembic migrations using the direct admin URL; configure Cloud Run runtime with the transaction-pooler URL copied from Supabase Connect output.

- [ ] **Step 2: Create Vercel project**

Project name: `toptenug-web`.

Root directory: `apps/web`.

Set Preview `NEXT_PUBLIC_API_BASE_URL` to staging Cloud Run only; no DB credential is added to Vercel.

- [ ] **Step 3: Deploy staging Cloud Run API/jobs**

Region: `europe-west3`.

Pin image/revision to Git commit SHA. Store backend secrets in Secret Manager and grant secret access only to the runtime service account.

- [ ] **Step 4: Configure schedules**

Initial staging schedules:

- discovery: weekly;
- GitHub ingestion: daily;
- provisional derive/preview: weekly;
- validation/publish: **no automatic production schedule**.

- [ ] **Step 5: Run staging smoke test and record evidence**

Run `scripts/smoke_phase2.py` and record service/project names, regions, commit SHA and smoke outcome only—no secret material.

- [ ] **Step 6: Commit deployment record**

Commit: `ops: record TopTenUG staging deployment`

---

### Task 12: Run the first Uganda GitHub developer discovery/review campaign

**Files:**
- Create/update: `docs/operations/data-campaigns/2026-q3-github-developers.md`
- No raw private data file is committed; candidate/evidence state lives in PostgreSQL.

**Interfaces:**
- Uses `discover --persist`, review commands and `report launch-readiness`.
- Produces a persisted review queue and auditable campaign counts.

- [ ] **Step 1: Seed discovery with diverse public-source queries**

Use multiple queries covering open source, backend/frontend/mobile, data/AI/ML, cloud/DevOps/security, Web3, university/community builders and diaspora. Search/Gemini ordering is not stored as rank.

- [ ] **Step 2: Continue discovery until `discovered >= 100`**

Deduplicate through candidate identity keys; report unique candidate count rather than raw proposal count.

- [ ] **Step 3: Review evidence candidate-by-candidate**

Approve only `UGANDAN_IN_UGANDA` or `UGANDAN_DIASPORA` with grounded evidence. Ambiguous candidates stay `REVIEW_REQUIRED`; do not infer nationality from name, appearance, language or LLM intuition.

- [ ] **Step 4: Reach launch pool**

Continue evidence review until at least 50 candidates are approved and category-eligible or explicitly record that the national launch gate is not yet met. Never lower the threshold to make publication easier.

- [ ] **Step 5: Record campaign summary**

Document counts by review state, common discovery gaps, source limitations and methodology caveats. Do not commit sensitive/private material.

- [ ] **Step 6: Commit campaign summary**

Commit: `docs: record Q3 developer discovery campaign`

---

### Task 13: Ingest real GitHub observations and publish the provisional public preview

**Files:**
- Update: `docs/operations/data-campaigns/2026-q3-github-developers.md`
- No manual rank file is created.

**Interfaces:**
- Uses `github-batch`, `derive`, `preview`, launch-readiness report and preview web/API.

- [ ] **Step 1: Batch-ingest all approved candidates**

Run until each approved candidate either has a successful ingestion record or a typed unresolved source failure.

- [ ] **Step 2: Rerun ingestion to prove idempotency**

Duplicate observation count must not inflate simply because a job was retried.

- [ ] **Step 3: Derive 2026-Q3 metrics using the Kampala cutoff utility**

Before quarter close the cutoff for provisional runs is the actual run timestamp, capped by the official quarter boundary.

- [ ] **Step 4: Create METRIC, INDEX and TREND preview outputs**

`DevRankUG` is INDEX. Direct METRIC ranking uses a declared GitHub metric. TREND requires two valid observation windows; if the campaign has not yet collected two valid windows, mark TREND unavailable rather than fabricate a baseline.

- [ ] **Step 5: Publish provisional web preview**

Verify explicit non-official banner, reviewed pool count, Top 10 default, 20/30/50 expansion, no official share cards and no provisional result on official API routes.

- [ ] **Step 6: Record preview run IDs/algorithm version and commit summary**

Commit: `docs: record Q3 provisional ranking preview`

---

### Task 14: Freeze, validate and publish the official 2026-Q3 snapshot after cutoff

**Time gate:** Do not execute the official-publish steps before **2026-09-30 23:59:59 Africa/Kampala** (`2026-09-30T21:00:00Z` exclusive boundary).

**Files:**
- Update: `docs/operations/data-campaigns/2026-q3-github-developers.md`
- Create: `docs/releases/2026-q3-github-developers.md`

**Interfaces:**
- Uses `derive`, `validate`, `report launch-readiness`, `publish`, official API/share surfaces.

- [ ] **Step 1: Freeze Q3 inputs**

Derive from observations strictly before `2026-09-30T21:00:00Z`. Record the cutoff and source/run IDs.

- [ ] **Step 2: Re-run launch readiness**

Do not proceed unless discovered >= 100, eligible/qualified >= 50, validation passes, blocking anomalies = 0 and unresolved duplicate conflicts = 0.

- [ ] **Step 3: Review proposed Top 50 before publication**

Review factor coverage, provenance, duplicate identity, anomaly and eligibility blockers. Review changes evidence/eligibility only; nobody manually edits `RankingResult.rank`.

- [ ] **Step 4: Publish one immutable official run**

Run:

```text
toptenug publish --category github-developers --quarter 2026-Q3
```

Expected: new `PUBLISHED` run; prior official run remains unchanged; provisional runs remain historical/non-official.

- [ ] **Step 5: Verify official public surfaces**

Run production smoke checks and verify:

- official endpoint returns PUBLISHED only;
- Top 10 default and 20/30/50 limits;
- profiles/methodology show algorithm version, coverage and safe evidence links;
- official share metadata derives from immutable published result IDs;
- provisional banner is absent from official pages.

- [ ] **Step 6: Produce release report**

`docs/releases/2026-q3-github-developers.md` records: cutoff, candidate universe size, eligible pool size, algorithm name/version, validation outcome, known limitations, publication run ID and deployment commit SHA. Do not copy secrets or private review notes.

- [ ] **Step 7: Commit release record**

Commit: `release: publish TopTenUG 2026 Q3 GitHub Developers snapshot`

---

## Phase 2 Acceptance Criteria

Phase 2 is complete only when all are demonstrated:

1. Vercel serves the Next.js public app and holds no production DB credential.
2. Cloud Run serves FastAPI and separate Cloud Run Jobs run operational commands.
3. Supabase PostgreSQL/pgvector is canonical durable storage.
4. Runtime and admin database connections are separated correctly.
5. Candidate discovery is persisted and deduplicated; discovery ordering has no ranking effect.
6. At least 100 plausible candidates are discovered before claiming national coverage for the first release.
7. At least 50 candidates are approved, category-eligible and qualified before the first official Top 50.
8. GitHub observations are immutable/provenanced and batch ingestion is retry-safe.
9. METRIC, INDEX and valid TREND outputs are computed by TopTenUG-owned code.
10. Provisional and published runs are structurally and visually distinct.
11. Q3 uses the Kampala boundary `2026-09-30T21:00:00Z` exclusive.
12. Publication before that boundary is rejected.
13. A failed validation/publication never replaces a prior official snapshot.
14. Official API and share-card surfaces accept PUBLISHED results only.
15. Web defaults to Top 10 and allows only 20/30/50 expansion.
16. Production/staging secrets are absent from Git and diagnostics/logs.
17. CI remains low-noise and deployment is a separate deliberate workflow.
18. Staging smoke tests prove health, DB connectivity, official/preview isolation and end-to-end fixture flow.
19. The official Q3 release record documents universe size, algorithm version, cutoff, limitations, run ID and deployment SHA.

## Self-Review Record

- **Spec coverage:** Sections 1–29 map to Tasks 1–14: runtime config/deployment, persistent candidate review, hard-metric batching, `PROVISIONAL` state, Kampala freeze semantics, launch thresholds, public preview UX, infrastructure, CI/CD, staging, discovery/review campaign, provisional data run and time-gated official release.
- **Step scan:** Each code task carries a failing-test → implementation → verification → commit cycle. Operational campaign tasks carry measurable gates and never ask an implementer to invent eligibility or ranking criteria.
- **Type consistency:** candidate persistence is `CandidateProposal -> CandidateRecord -> Entity/Evidence/SourceAccount`; ranking remains `Observation -> DerivedMetric/CandidateMetrics -> ScoredCandidate -> RankingResult`; provisional and published use the same deterministic score engine but different immutable runs/status surfaces.
- **Review Focus coverage:** provisional leakage (Task 5), Kampala boundary (Task 6), duplicate discovery (Task 3), partial GitHub failures (Task 4), environment misrouting (Tasks 1/9) all have explicit tests.
- **Proportion:** deployment and live-data campaign details are specified at interface/gate level; no task embeds production credentials, generated project refs, or full implementation bodies.
- **Deferred intentionally:** other universes, semantic search UI, MCP, A2A, Ranking Lab and a polished admin console remain follow-on work.
