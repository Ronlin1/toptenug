# TopTenUG MVP Vertical Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a working TopTenUG MVP that continuously ingests evidence for a first Uganda technology/open-source ranking family, computes TopTenUG-owned deterministic METRIC/INDEX/TREND rankings, freezes official quarterly snapshots, and exposes them through a polished public dashboard, profiles, methodology pages, and downloadable/shareable cards.

**Architecture:** Use a small monorepo with a Next.js public web application and a Python FastAPI/data service backed by PostgreSQL + pgvector. Direct source adapters and the Google/Gemini intelligence layer feed an evidence/observation store; only the TopTenUG ranking engine can turn normalized stored metrics into official ranks. The first vertical is Technology & Builders / GitHub & Open Source, proving the generic architecture before more universes are added.

**Tech Stack:** Next.js App Router + TypeScript + Tailwind CSS + shadcn/ui + Recharts; Python 3.13+ + FastAPI + Pydantic v2 + SQLAlchemy 2 + Alembic + httpx + `google-genai` + PyYAML; PostgreSQL 16+ + pgvector; Docker Compose; `pnpm`; `uv`; pytest + Ruff + mypy; Vitest/Testing Library + Playwright; GitHub Actions; deployment target Google Cloud Run + Cloud SQL + Cloud Scheduler + Secret Manager.

**Spec:** `docs/superpowers/specs/2026-09-23-toptenug-design.md`

## Global Constraints

- **Ranking ownership:** Google/Gemini, search engines, source APIs, journals, public datasets, and scraped public pages provide inputs/evidence only. They never directly assign an official TopTenUG rank.
- **Official algorithm invariant:** `AI interprets evidence; TopTenUG calculates rankings.` All official ranks come from versioned deterministic TopTenUG code/config operating on stored metrics.
- **Ranking types:** every leaderboard is explicitly `METRIC`, `INDEX`, or `TREND`.
- **Quarterly stability:** continuously ingested data never silently rewrites an official quarterly snapshot.
- **Public list size:** every leaderboard defaults to 10 and supports only 10, 20, 30, or 50 public rows.
- **Provenance:** no official ranking input exists without source, retrieval time, and evidence/observation provenance.
- **AI boundary:** Gemini output is structured as proposals/extractions and must be grounded in Levels A-D evidence before it can affect official metrics.
- **Eligibility:** Uganda relationship/eligibility is explicit, evidence-backed, and independent from ranking strength.
- **Correction model:** correct underlying evidence/observations and recompute; do not manually edit published rank numbers.
- **Privacy/source ethics:** use public, relevant data only; no bypassing access controls or ingesting private/sensitive data unrelated to the public ranking purpose.
- **Contribution model:** methodology changes are versioned and documented; source/ranking proposals remain reviewable through repository workflows.
- **First vertical only:** this plan proves the architecture with Technology & Builders / GitHub & Open Source. Media, startups, creators, digital marketing, research, MCP, and A2A are out of scope for this implementation plan and receive follow-on plans after this vertical is stable.

## Review Focus

1. **Ambiguous Uganda eligibility:** an entity with insufficient or conflicting eligibility evidence must remain discoverable but cannot enter an official Uganda leaderboard.
2. **Missing metrics:** missing source data follows the algorithm specification's explicit missing-data policy and must never silently become numeric zero unless zero is semantically correct.
3. **Abnormal metric jumps:** extreme source changes are preserved as observations but must be flagged before they can dominate an official quarterly snapshot.
4. **AI ranking leakage:** Gemini/search output containing phrases such as “#1” or an ordered candidate list must not populate `RankingResult.rank`; the engine recomputes ranks solely from stored normalized inputs.
5. **Partial/failed quarter pipeline:** a failed validation or critical coverage gate must leave the previous official snapshot intact and must not expose a partially published quarter.

---

## File Structure

```text
toptenug/
├── apps/
│   └── web/
│       ├── app/
│       │   ├── page.tsx
│       │   ├── technology/page.tsx
│       │   ├── technology/github-developers/page.tsx
│       │   ├── people/[slug]/page.tsx
│       │   ├── methodology/[slug]/page.tsx
│       │   └── api/share/[rankingResultId]/route.tsx
│       ├── components/
│       │   ├── category-card.tsx
│       │   ├── leaderboard.tsx
│       │   ├── ranking-row.tsx
│       │   ├── metric-card.tsx
│       │   ├── rank-history-chart.tsx
│       │   ├── score-breakdown.tsx
│       │   └── share-ranking.tsx
│       ├── lib/api.ts
│       └── tests/
├── services/
│   └── core/
│       ├── pyproject.toml
│       ├── app/
│       │   ├── main.py
│       │   ├── config.py
│       │   ├── db.py
│       │   ├── domain/
│       │   │   ├── enums.py
│       │   │   ├── schemas.py
│       │   │   └── models.py
│       │   ├── ranking/
│       │   │   ├── engine.py
│       │   │   ├── normalizers.py
│       │   │   ├── metric.py
│       │   │   ├── index.py
│       │   │   ├── trend.py
│       │   │   └── loader.py
│       │   ├── sources/
│       │   │   ├── base.py
│       │   │   └── github.py
│       │   ├── intelligence/
│       │   │   ├── base.py
│       │   │   └── gemini.py
│       │   ├── ingestion/
│       │   │   ├── pipeline.py
│       │   │   ├── entity_resolution.py
│       │   │   └── eligibility.py
│       │   ├── quarterly/
│       │   │   ├── validate.py
│       │   │   └── publish.py
│       │   ├── api/
│       │   │   ├── rankings.py
│       │   │   ├── entities.py
│       │   │   ├── dashboard.py
│       │   │   └── methodology.py
│       │   └── cli.py
│       ├── algorithms/
│       │   └── devrankug/v1.0.0.yaml
│       ├── migrations/
│       └── tests/
├── infra/
│   ├── docker-compose.yml
│   └── cloudrun/
├── .github/workflows/ci.yml
└── docs/methodology/devrankug-v1.md
```

Each Python module owns one concern: source collection, intelligence proposals, ingestion/orchestration, deterministic ranking, or publication. The web app consumes API contracts and never calculates official rankings in the browser.

---

### Task 1: Bootstrap the monorepo and executable health checks

**Files:**
- Create: `apps/web/package.json`
- Create: `apps/web/app/page.tsx`
- Create: `apps/web/app/layout.tsx`
- Create: `apps/web/lib/api.ts`
- Create: `services/core/pyproject.toml`
- Create: `services/core/app/main.py`
- Create: `services/core/app/config.py`
- Create: `services/core/tests/test_health.py`
- Create: `infra/docker-compose.yml`
- Create: `.github/workflows/ci.yml`
- Create: `pnpm-workspace.yaml`

**Interfaces:**
- Produces: `GET /health -> {"status":"ok"}` from FastAPI.
- Produces: `NEXT_PUBLIC_API_BASE_URL`-driven `apiGet<T>(path: string): Promise<T>` in the web app.

- [ ] **Step 1: Write the failing API health test**

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: Run the test and verify the service is not implemented**

Run: `cd services/core && uv run pytest tests/test_health.py -v`

Expected: FAIL because `app.main` or `/health` does not exist.

- [ ] **Step 3: Create the minimal FastAPI application**

```python
from fastapi import FastAPI

app = FastAPI(title="TopTenUG Core", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 4: Add local PostgreSQL + pgvector and web/api development commands**

`infra/docker-compose.yml` must expose PostgreSQL locally, persist a named volume, and enable the `vector` extension during database initialization. `apps/web` must start with `pnpm dev`; `services/core` must start with `uv run fastapi dev app/main.py`.

- [ ] **Step 5: Add CI checks**

CI runs, at minimum:

```bash
cd services/core && uv run ruff check .
cd services/core && uv run mypy app
cd services/core && uv run pytest -q
pnpm --dir apps/web lint
pnpm --dir apps/web test
```

- [ ] **Step 6: Run the complete bootstrap verification**

Expected: API health test PASS, web lint/test PASS, PostgreSQL container healthy.

- [ ] **Step 7: Commit**

```bash
git add apps services infra .github pnpm-workspace.yaml
git commit -m "chore: bootstrap TopTenUG monorepo"
```

---

### Task 2: Implement the evidence-first domain model and database schema

**Files:**
- Create: `services/core/app/domain/enums.py`
- Create: `services/core/app/domain/schemas.py`
- Create: `services/core/app/domain/models.py`
- Create: `services/core/app/db.py`
- Create: `services/core/migrations/versions/0001_core_domain.py`
- Create: `services/core/tests/domain/test_models.py`

**Interfaces:**
- Produces enums: `EntityType`, `RankingType`, `EvidenceLevel`, `UgandaRelation`, `ReviewStatus`, `RankingRunStatus`.
- Produces tables/models: `Entity`, `EntityAlias`, `Source`, `SourceAccount`, `Evidence`, `Observation`, `MetricDefinition`, `DerivedMetric`, `RankingCategory`, `AlgorithmDefinition`, `RankingRun`, `RankingResult`, `IngestionRun`.
- Produces schema: `ObservationInput(metric_key: str, raw_value: float | int | str, observed_at: datetime, source_url: str, evidence_id: UUID)`.

- [ ] **Step 1: Write schema tests for provenance and eligibility**

```python
def test_observation_requires_source_url_and_evidence_id():
    with pytest.raises(ValidationError):
        ObservationInput(
            metric_key="github.followers",
            raw_value=120,
            observed_at=datetime.now(UTC),
        )


def test_entity_can_be_discoverable_without_being_eligible():
    entity = EntityCreate(name="Example", entity_type=EntityType.PERSON)
    assert entity.is_discoverable is True
    assert entity.is_eligible is False
```

- [ ] **Step 2: Run the tests and confirm failure**

Run: `cd services/core && uv run pytest tests/domain/test_models.py -v`

Expected: FAIL because the domain schemas do not exist.

- [ ] **Step 3: Implement enums and Pydantic contracts**

Use explicit enums and UUID identifiers. Do not represent eligibility as a free-text string. `Evidence` stores `level`, `source_url`, `retrieved_at`, `claim`, `confidence`, and optional content hash. `Observation` stores immutable source facts; updates create new rows.

- [ ] **Step 4: Implement SQLAlchemy models and migration**

Important constraints:

```text
UNIQUE(source_id, source_record_id, metric_key, observed_at)
UNIQUE(ranking_run_id, entity_id)
UNIQUE(ranking_run_id, rank)
CHECK(rank >= 1)
CHECK(confidence >= 0 AND confidence <= 1)
```

`RankingResult` references a completed `RankingRun`; `RankingRun` references a category and algorithm version.

- [ ] **Step 5: Test migration up/down and provenance rules**

Run:

```bash
cd services/core
uv run alembic upgrade head
uv run pytest tests/domain/test_models.py -v
uv run alembic downgrade base
uv run alembic upgrade head
```

Expected: all commands succeed.

- [ ] **Step 6: Commit**

```bash
git add services/core/app/domain services/core/app/db.py services/core/migrations services/core/tests/domain
git commit -m "feat: add evidence-first domain model"
```

---

### Task 3: Build the TopTenUG-owned deterministic ranking engine

**Files:**
- Create: `services/core/app/ranking/normalizers.py`
- Create: `services/core/app/ranking/metric.py`
- Create: `services/core/app/ranking/index.py`
- Create: `services/core/app/ranking/trend.py`
- Create: `services/core/app/ranking/loader.py`
- Create: `services/core/app/ranking/engine.py`
- Create: `services/core/algorithms/devrankug/v1.0.0.yaml`
- Create: `services/core/tests/ranking/test_engine.py`
- Create: `services/core/tests/ranking/test_normalizers.py`
- Create: `docs/methodology/devrankug-v1.md`

**Interfaces:**
- Consumes: stored/validated `DerivedMetric` values only.
- Produces: `RankingEngine.run(spec: AlgorithmSpec, candidates: list[CandidateMetrics]) -> list[ScoredCandidate]`.
- Produces: deterministic `score`, `rank`, and `factor_breakdown`.
- Must not import `google.genai`, web/search clients, or source adapters.

- [ ] **Step 1: Write failing tests for deterministic ranking, missing data, ties, and AI isolation**

```python
def test_same_inputs_produce_same_order(engine, devrank_spec, candidates):
    assert engine.run(devrank_spec, candidates) == engine.run(devrank_spec, candidates)


def test_missing_metric_uses_declared_policy(engine, devrank_spec):
    candidate = CandidateMetrics(entity_id=uuid4(), metrics={"github.followers": None})
    result = engine.run(devrank_spec, [candidate])[0]
    assert result.factor_breakdown["audience"].missing_policy == "renormalize_available"


def test_engine_has_no_ai_dependency():
    source = Path("app/ranking/engine.py").read_text()
    assert "google.genai" not in source
    assert "Gemini" not in source
```

Also test stable tie-breaking by canonical entity UUID after score tie.

- [ ] **Step 2: Run ranking tests and confirm failure**

Run: `cd services/core && uv run pytest tests/ranking -v`

Expected: FAIL because ranking modules/config are absent.

- [ ] **Step 3: Implement pure normalizers**

Support exact configured operations:

```python
log1p
percentile
robust_z
min_max
capped_min_max
```

Each function accepts the candidate universe for the current run and returns deterministic floats in the documented range.

- [ ] **Step 4: Add `DevRankUG 1.0.0` configuration**

The initial index uses only GitHub-derived hard metrics so its behavior can be validated:

```yaml
name: DevRankUG
version: 1.0.0
ranking_type: INDEX
eligibility_policy: ugandan_or_uganda_based_technology_builder
missing_data_policy: renormalize_available
minimum_factor_coverage: 0.60
tie_breaker: canonical_entity_id
factors:
  project_adoption:
    weight: 0.30
    metric: github.owned_repo_stars
    normalization: log1p
  contribution_activity:
    weight: 0.25
    metric: github.contributions_90d
    normalization: percentile
  project_breadth:
    weight: 0.15
    metric: github.active_owned_repos_180d
    normalization: capped_min_max
  audience:
    weight: 0.10
    metric: github.followers
    normalization: log1p
  collaboration:
    weight: 0.20
    metric: github.prs_and_reviews_90d
    normalization: percentile
```

No Gemini/Search output is a factor.

- [ ] **Step 5: Implement METRIC, INDEX, and TREND evaluators**

`METRIC` sorts a declared observable metric after eligibility/coverage checks. `INDEX` calculates configured normalized weighted factors. `TREND` compares the same metric/index across two defined observation windows and rejects candidates missing a valid baseline.

- [ ] **Step 6: Document methodology**

`docs/methodology/devrankug-v1.md` explains candidate universe, formula, weights, normalization, missing-data behavior, tie-breaks, limitations, and why search/AI relevance is not a ranking signal.

- [ ] **Step 7: Run the tests**

Run: `cd services/core && uv run pytest tests/ranking -v`

Expected: PASS, including deterministic replay.

- [ ] **Step 8: Commit**

```bash
git add services/core/app/ranking services/core/algorithms services/core/tests/ranking docs/methodology
git commit -m "feat: add deterministic TopTenUG ranking engine"
```

---

### Task 4: Implement the source-adapter contract and GitHub hard-metric ingestion

**Files:**
- Create: `services/core/app/sources/base.py`
- Create: `services/core/app/sources/github.py`
- Create: `services/core/tests/sources/test_github.py`
- Modify: `services/core/app/config.py`

**Interfaces:**
- Produces protocol: `SourceAdapter.collect(entity: EntityRef) -> list[ObservationInput]`.
- Produces `GitHubAdapter` metrics: `github.followers`, `github.owned_repo_stars`, `github.active_owned_repos_180d`, `github.contributions_90d`, `github.prs_and_reviews_90d`.
- Every observation includes GitHub URL, retrieval timestamp, and evidence reference.

- [ ] **Step 1: Write contract tests with mocked GitHub HTTP/GraphQL responses**

Test non-fork repository filtering, contribution-window calculation, rate-limit responses, missing profile handling, and provenance attachment.

```python
async def test_github_adapter_never_returns_unprovenanced_observation(adapter):
    rows = await adapter.collect(EntityRef(id=uuid4(), external_id="octocat"))
    assert rows
    assert all(row.source_url and row.evidence_id for row in rows)
```

- [ ] **Step 2: Run tests and verify failure**

Run: `cd services/core && uv run pytest tests/sources/test_github.py -v`

- [ ] **Step 3: Implement GitHub adapter**

Use GitHub's API for hard metrics. Do not scrape GitHub HTML when the API supplies the metric. Convert HTTP 403/429 into typed retryable source errors carrying reset/retry metadata.

- [ ] **Step 4: Verify no ranking is calculated in the adapter**

The adapter output may contain source metrics only. Add a test asserting it has no `rank` or `score` field.

- [ ] **Step 5: Commit**

```bash
git add services/core/app/sources services/core/tests/sources services/core/app/config.py
git commit -m "feat: ingest GitHub ranking inputs"
```

---

### Task 5: Add Google/Gemini as a support-only intelligence layer

**Files:**
- Create: `services/core/app/intelligence/base.py`
- Create: `services/core/app/intelligence/gemini.py`
- Create: `services/core/tests/intelligence/test_gemini_contract.py`
- Modify: `services/core/app/config.py`

**Interfaces:**
- Produces protocol: `IntelligenceProvider.discover(query: DiscoveryQuery) -> list[CandidateProposal]`.
- Produces: `extract_evidence(url: str, schema: type[T]) -> list[T]`.
- `CandidateProposal` fields include `display_name`, `entity_type`, `candidate_profiles`, `uganda_relation_claims`, `source_urls`, `confidence`; it has no official `rank` field.

- [ ] **Step 1: Write failing contract tests proving Google/Gemini cannot create an official rank**

```python
def test_candidate_proposal_has_no_official_rank_field():
    assert "rank" not in CandidateProposal.model_fields
    assert "official_score" not in CandidateProposal.model_fields


def test_discovery_order_is_not_persisted_as_rank(fake_gemini, repository):
    proposals = fake_gemini.discover(DiscoveryQuery(text="Ugandan open source developers"))
    saved = repository.save_candidate_proposals(proposals)
    assert all(row.official_rank is None for row in saved)
```

- [ ] **Step 2: Run and verify failure**

Run: `cd services/core && uv run pytest tests/intelligence -v`

- [ ] **Step 3: Implement the provider abstraction and Gemini implementation**

Use structured output schemas. Google Search grounding/URL research may discover sources and claims. Persist citations/source URLs with every accepted extraction. Treat model-only unsupported claims as proposals requiring evidence, never as official observations.

- [ ] **Step 4: Add confidence and grounding rules**

Reject any proposal that has no Level A-D `source_urls`. Mark ambiguous identity/eligibility proposals `REVIEW_REQUIRED`; do not auto-approve them.

- [ ] **Step 5: Commit**

```bash
git add services/core/app/intelligence services/core/tests/intelligence services/core/app/config.py
git commit -m "feat: add Gemini intelligence support layer"
```

---

### Task 6: Build ingestion, entity resolution, and Uganda eligibility gates

**Files:**
- Create: `services/core/app/ingestion/pipeline.py`
- Create: `services/core/app/ingestion/entity_resolution.py`
- Create: `services/core/app/ingestion/eligibility.py`
- Create: `services/core/tests/ingestion/test_pipeline.py`
- Create: `services/core/tests/ingestion/test_eligibility.py`

**Interfaces:**
- Consumes: `CandidateProposal`, source-adapter `ObservationInput`, existing entities/evidence.
- Produces: persisted candidates, evidence, immutable observations, and explicit eligibility decisions.
- Produces: `EligibilityDecision(eligible: bool, relation: UgandaRelation | None, evidence_ids: list[UUID], status: ReviewStatus)`.

- [ ] **Step 1: Write failure-mode tests**

Cover duplicate aliases, conflicting Uganda evidence, source failure preserving previous observation, and an ambiguous entity refusing auto-merge.

```python
def test_conflicting_uganda_evidence_blocks_official_eligibility(service):
    decision = service.evaluate(conflicting_evidence_fixture)
    assert decision.eligible is False
    assert decision.status == ReviewStatus.REVIEW_REQUIRED
```

- [ ] **Step 2: Run and verify failure**

Run: `cd services/core && uv run pytest tests/ingestion -v`

- [ ] **Step 3: Implement idempotent ingestion**

Use source record identifiers/content hashes to avoid duplicate observations on retries. Never mutate an older observation to represent new source state.

- [ ] **Step 4: Implement conservative identity/eligibility rules**

High-confidence deterministic identifiers may auto-link; conflicting/ambiguous matches remain separate until review. A discovered candidate may appear in search but must have `eligible=False` until its ranking-specific Uganda policy is satisfied.

- [ ] **Step 5: Run tests and commit**

```bash
cd services/core && uv run pytest tests/ingestion -v
git add services/core/app/ingestion services/core/tests/ingestion
git commit -m "feat: add ingestion and eligibility gates"
```

---

### Task 7: Implement quarterly validation, anomaly gates, and immutable publication

**Files:**
- Create: `services/core/app/quarterly/validate.py`
- Create: `services/core/app/quarterly/publish.py`
- Create: `services/core/tests/quarterly/test_publish.py`
- Create: `services/core/tests/quarterly/test_validation.py`

**Interfaces:**
- Produces: `QuarterPublisher.publish(quarter: Quarter, category_id: UUID, algorithm_version: str) -> RankingRun`.
- Publication transitions `DRAFT -> VALIDATING -> PUBLISHED` atomically; failures become `FAILED` and expose no official results.

- [ ] **Step 1: Write tests for atomic publication and anomaly blocking**

```python
def test_failed_validation_keeps_previous_snapshot_official(publisher, previous_run):
    with pytest.raises(QuarterValidationError):
        publisher.publish(Quarter(2026, 3), category_id, "1.0.0")
    assert publisher.current_official(category_id).id == previous_run.id


def test_extreme_jump_is_flagged_before_publish(validator):
    report = validator.validate(anomalous_fixture)
    assert report.blocking_anomalies
```

- [ ] **Step 2: Run and verify failure**

Run: `cd services/core && uv run pytest tests/quarterly -v`

- [ ] **Step 3: Implement validation gates**

Validate: eligible candidate set, metric coverage, provenance, stale critical sources, rank uniqueness, algorithm version, factor coverage, impossible values, and configured anomaly thresholds.

- [ ] **Step 4: Implement transactional snapshot publication**

Compute results into a draft run, validate all rows, then publish in one database transaction. Do not delete prior official runs.

- [ ] **Step 5: Add deterministic replay test**

Re-running the engine against the frozen same inputs and algorithm version must reproduce the same ordered entity IDs and scores within configured numeric precision.

- [ ] **Step 6: Commit**

```bash
git add services/core/app/quarterly services/core/tests/quarterly
git commit -m "feat: publish immutable quarterly ranking snapshots"
```

---

### Task 8: Expose the public read API

**Files:**
- Create: `services/core/app/api/rankings.py`
- Create: `services/core/app/api/entities.py`
- Create: `services/core/app/api/dashboard.py`
- Create: `services/core/app/api/methodology.py`
- Create: `services/core/tests/api/test_rankings.py`
- Modify: `services/core/app/main.py`

**Interfaces:**
- `GET /v1/dashboard`
- `GET /v1/rankings/{slug}?limit=10|20|30|50&quarter=YYYY-QN`
- `GET /v1/entities/{slug}`
- `GET /v1/entities/{slug}/history`
- `GET /v1/methodology/{slug}`
- `GET /v1/quarters`

- [ ] **Step 1: Write API tests for limit enforcement and official-only output**

```python
@pytest.mark.parametrize("limit", [10, 20, 30, 50])
def test_supported_public_limits(client, limit):
    response = client.get(f"/v1/rankings/github-developers?limit={limit}")
    assert response.status_code == 200
    assert len(response.json()["results"]) <= limit


def test_limit_above_50_is_rejected(client):
    assert client.get("/v1/rankings/github-developers?limit=51").status_code == 422
```

Also assert draft/provisional `RankingRun`s are never returned by the public endpoint.

- [ ] **Step 2: Run tests and verify failure**

- [ ] **Step 3: Implement read endpoints with stable response schemas**

Each ranking response includes `quarter`, `ranking_type`, `algorithm_name`, `algorithm_version`, `published_at`, `methodology_url`, and result-level provenance/confidence summary.

- [ ] **Step 4: Run API tests and OpenAPI schema check**

Run: `cd services/core && uv run pytest tests/api -v`

- [ ] **Step 5: Commit**

```bash
git add services/core/app/api services/core/app/main.py services/core/tests/api
git commit -m "feat: expose TopTenUG public ranking API"
```

---

### Task 9: Build the premium discovery UI and first leaderboard route

**Files:**
- Create/Modify: `apps/web/app/page.tsx`
- Create: `apps/web/app/technology/page.tsx`
- Create: `apps/web/app/technology/github-developers/page.tsx`
- Create: `apps/web/components/category-card.tsx`
- Create: `apps/web/components/leaderboard.tsx`
- Create: `apps/web/components/ranking-row.tsx`
- Create: `apps/web/components/metric-card.tsx`
- Create: `apps/web/tests/leaderboard.test.tsx`
- Modify: `apps/web/lib/api.ts`

**Interfaces:**
- Consumes the `/v1/dashboard` and `/v1/rankings/*` API only.
- Produces Top 10 default and explicit Top 20/30/50 selection.

- [ ] **Step 1: Write UI tests**

Test default Top 10, allowed limit controls, quarter/ranking-type badge, rank movement, methodology link, and empty/error state.

- [ ] **Step 2: Run tests and verify failure**

Run: `pnpm --dir apps/web test`

- [ ] **Step 3: Implement homepage and Technology universe route**

Homepage shows TopTenUG identity/current quarter, digital pulse metrics, trending/movers sections, and category cards. Keep the landing page discovery-oriented; do not dump raw database tables.

- [ ] **Step 4: Implement GitHub Developers leaderboard**

Display rank, movement, person/avatar, key score/metric, type badge, quarter, confidence indicator, share action, profile link, and methodology link.

- [ ] **Step 5: Verify responsive behavior**

Run Playwright at mobile, tablet, and desktop viewport sizes; the Top 10 remains usable without horizontal scrolling.

- [ ] **Step 6: Commit**

```bash
git add apps/web
git commit -m "feat: add TopTenUG discovery and leaderboard UI"
```

---

### Task 10: Add profiles, methodology, and interactive analytics

**Files:**
- Create: `apps/web/app/people/[slug]/page.tsx`
- Create: `apps/web/app/methodology/[slug]/page.tsx`
- Create: `apps/web/components/rank-history-chart.tsx`
- Create: `apps/web/components/score-breakdown.tsx`
- Create: `apps/web/tests/profile.test.tsx`

**Interfaces:**
- Consumes entity/history/methodology endpoints.
- No client component computes official score or rank.

- [ ] **Step 1: Write profile tests**

Test current rankings, previous-quarter movement, score history, factor breakdown, public evidence links, confidence/coverage, and methodology version.

- [ ] **Step 2: Implement profile and methodology pages**

The methodology page must expose the exact versioned factors/weights and known limitations used by the official snapshot.

- [ ] **Step 3: Add actionable charts**

Clicking a rank-history point navigates/selects the corresponding quarter where available. Charts are accessible with text/tabular equivalents for core values.

- [ ] **Step 4: Verify and commit**

```bash
pnpm --dir apps/web test
git add apps/web
git commit -m "feat: add ranking profiles and methodology analytics"
```

---

### Task 11: Build official downloadable/shareable ranking cards

**Files:**
- Create: `apps/web/app/api/share/[rankingResultId]/route.tsx`
- Create: `apps/web/components/share-ranking.tsx`
- Create: `apps/web/tests/share-ranking.test.tsx`
- Create: `services/core/tests/api/test_share_metadata.py`
- Modify: `services/core/app/api/rankings.py`

**Interfaces:**
- Card input is an immutable published `rankingResultId`; arbitrary client-provided rank/score text is rejected.
- Formats: `square`, `portrait`, `story`, `landscape`.
- Actions: PNG/WebP download where supported, copy canonical link, Web Share API/native share where available.

- [ ] **Step 1: Write tamper-resistance tests**

```python
def test_share_metadata_comes_from_published_result(client, published_result):
    payload = client.get(f"/v1/rankings/results/{published_result.id}/share").json()
    assert payload["rank"] == published_result.rank
    assert payload["score"] == published_result.score
```

UI test: supplying `?rank=1` must not alter the rendered card's official rank.

- [ ] **Step 2: Implement server-generated social image route**

Use canonical published metadata from the API. Render TopTenUG branding, rank, category, quarter, movement/milestone, entity name, and canonical URL/QR-compatible destination.

- [ ] **Step 3: Implement download/share controls**

Use the Web Share API when available; otherwise expose image download and copy-link fallbacks. Generate OpenGraph metadata from the same canonical result.

- [ ] **Step 4: Test all four aspect ratios and commit**

```bash
pnpm --dir apps/web test
cd services/core && uv run pytest tests/api/test_share_metadata.py -v
git add apps/web services/core
git commit -m "feat: add official ranking share cards"
```

---

### Task 12: Add CLI jobs, scheduling boundaries, observability, and end-to-end proof

**Files:**
- Create: `services/core/app/cli.py`
- Create: `services/core/tests/e2e/test_first_vertical.py`
- Create: `infra/cloudrun/core.Dockerfile`
- Create: `infra/cloudrun/worker.Dockerfile`
- Create: `docs/operations/quarterly-runbook.md`
- Modify: `.github/workflows/ci.yml`

**Interfaces:**
- Commands:
  - `toptenug discover --universe technology`
  - `toptenug ingest github --entity <uuid>`
  - `toptenug derive --quarter YYYY-QN`
  - `toptenug validate --category github-developers --quarter YYYY-QN`
  - `toptenug publish --category github-developers --quarter YYYY-QN`
- Google Cloud Scheduler triggers jobs; the scheduler never contains ranking logic.

- [ ] **Step 1: Write the end-to-end test first**

Use deterministic fixture responses for Gemini discovery and GitHub source data. The test must execute:

```text
candidate discovery
→ evidence persistence
→ eligibility approval fixture
→ raw observations
→ derived metrics
→ DevRankUG execution
→ validation
→ official quarterly publish
→ GET leaderboard
→ GET profile/history
→ GET share metadata
```

Assertions include: rank determinism, algorithm version, provenance presence, Top 10 response limit, and zero dependency on Gemini discovery order.

- [ ] **Step 2: Run the E2E test and verify failure**

Run: `cd services/core && uv run pytest tests/e2e/test_first_vertical.py -v`

- [ ] **Step 3: Implement CLI orchestration**

CLI functions call existing services; do not duplicate source/ranking logic. Every job records `IngestionRun`/`RankingRun` status, start/end time, counts, and typed failure details.

- [ ] **Step 4: Add Cloud Run container definitions and scheduler runbook**

Document Secret Manager keys, GitHub token scopes, Gemini key/project configuration, Cloud SQL connection, quarter-close sequence, rollback behavior, and the rule that a failed publish leaves the prior quarter official.

- [ ] **Step 5: Extend CI with E2E fixture pipeline**

Run migrations against an ephemeral PostgreSQL service, then the full fixture E2E test. No live API keys are required in CI.

- [ ] **Step 6: Run the complete verification suite**

```bash
cd services/core && uv run ruff check .
cd services/core && uv run mypy app
cd services/core && uv run pytest -q
pnpm --dir apps/web lint
pnpm --dir apps/web test
pnpm --dir apps/web exec playwright test
```

Expected: all PASS.

- [ ] **Step 7: Commit**

```bash
git add services/core infra docs/operations .github/workflows/ci.yml
git commit -m "feat: complete TopTenUG MVP ranking vertical"
```

---

## MVP Acceptance Criteria

The implementation is complete only when all of the following are demonstrated from one reproducible fixture/live-development flow:

1. At least one Ugandan technology-builder entity has evidence-backed eligibility.
2. GitHub hard metrics are stored as immutable observations with provenance.
3. Gemini/Google can discover or structure candidate evidence but cannot create official score/rank fields.
4. A direct `METRIC` leaderboard is produced from an observable GitHub metric.
5. `DevRankUG 1.0.0` produces a deterministic `INDEX` ranking from versioned TopTenUG-owned factors.
6. A `TREND` ranking can compare two valid snapshots/windows.
7. An official quarterly snapshot survives subsequent ingestion unchanged.
8. The public API returns only published runs and enforces 10/20/30/50 limits.
9. The web app renders the homepage, Technology category, leaderboard, profile/history, and methodology.
10. A share card is generated only from immutable published ranking data and can be downloaded/shared.
11. A failed validation/publish attempt leaves the prior official snapshot intact.
12. CI proves the full source→evidence→metrics→TopTenUG algorithm→snapshot→API flow without external network calls.

## Follow-on plans after this vertical

These are deliberately separate implementation plans, not hidden work inside the MVP:

- **Media & Creators vertical:** YouTube Data API, radio/TV/media entities, social/public audience metrics, `CreatorRankUG`, `MediaRankUG`.
- **Startups & Digital Economy vertical:** startup/company discovery, public company/product evidence, `StartupRankUG`.
- **Research & Knowledge vertical:** OpenAlex/Crossref/ORCID and `ResearchRankUG`.
- **Semantic search:** pgvector embeddings, Google/Vertex retrieval support, structured + semantic exploration.
- **MCP server:** read-only TopTenUG tools over published rankings/evidence.
- **A2A orchestration:** specialist discovery/research agents coordinating through explicit contracts.
- **Ranking Lab:** user-adjustable unofficial simulations that never modify official snapshots.

## Self-Review Record

- **Spec coverage:** The first-cycle requirements are covered by Tasks 1-12: generic entities, evidence/provenance, direct metric ranking, composite index, trend ranking, historical observations, quarterly snapshots, Gemini-assisted discovery/extraction, dashboard, category, profile, Top 10→50, share cards, methodology, corrections-by-source architecture, and contributor-safe versioning boundaries.
- **Intentional scope exclusions:** Additional universes, semantic search, MCP, A2A, and Ranking Lab are explicitly deferred to named follow-on plans rather than partially implemented.
- **Placeholder scan:** No implementation step depends on TBD/TODO placeholders; concrete interfaces, tests, commands, and first algorithm factors are specified.
- **Type consistency:** Ranking inputs flow `ObservationInput -> DerivedMetric/CandidateMetrics -> ScoredCandidate -> RankingResult`; AI flows only `CandidateProposal/Evidence` and cannot supply `RankingResult.rank`.
- **Review Focus coverage:** ambiguous eligibility is covered in Task 6; missing metrics and AI isolation in Task 3/5; anomalies in Task 7; partial publication in Task 7; end-to-end integration in Task 12.
