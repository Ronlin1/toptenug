# TopTenUG Phase 2 — Live Data & Public Preview Design

**Date:** 2026-09-26  
**Branch:** `feat/phase2-live-data`  
**Depends on:** `feat/toptenug-mvp-vertical`  
**Status:** Self-reviewed; written-spec user review pending

## 1. Purpose

Phase 2 turns the verified TopTenUG Technology/GitHub MVP from a deterministic fixture-backed system into a live, real-data public product.

The first production vertical remains deliberately narrow:

> **Technology → GitHub Developers → Uganda**

The goal is not to launch every TopTenUG universe at once. The goal is to prove that TopTenUG can discover real Ugandan technology builders, preserve evidence and observations, calculate rankings with TopTenUG-owned algorithms, publish an auditable quarterly snapshot, and serve a polished public experience from production infrastructure.

## 2. Non-negotiable ranking invariant

External systems provide evidence and inputs. They do not provide official ranking decisions.

```text
Google Search / Gemini / GitHub / public web / datasets
                         ↓
                 evidence + metrics
                         ↓
                  TopTenUG database
                         ↓
              TopTenUG ranking engine
                         ↓
             official quarterly snapshot
```

The following are prohibited as direct official ranking signals:

- Google Search result position.
- Gemini/LLM opinion about who is more important, influential, talented, or deserving.
- An LLM-generated score or rank.
- Number of Google search-result hits.
- An unsupported inference about Uganda identity or residence.

Gemini may discover candidates, extract structured facts, classify evidence, suggest entity matches, explain already-computed results, and flag anomalies for review. The final score and rank must remain deterministic, versioned TopTenUG computation.

## 3. Phase 2 success criteria

Phase 2 is complete when all of the following are demonstrated in production or a production-equivalent staging environment:

1. The Next.js public app is deployed to Vercel.
2. The FastAPI public API is deployed to Google Cloud Run.
3. Long-running discovery/ingestion/derive/validate/publish operations run as Cloud Run Jobs.
4. Supabase PostgreSQL is the persistent production database and `pgvector` is enabled for future semantic retrieval.
5. Runtime secrets are not committed to Git and are supplied through managed environment/secret systems.
6. At least **100 plausible Uganda-linked GitHub developer candidates** are discovered for review before claiming a national first release.
7. At least **50 candidates** have sufficient evidence to reach an approved Uganda-eligibility state and satisfy the GitHub Developers category requirements before the first official national Top 50 is published.
8. GitHub hard metrics are ingested with immutable provenance and timestamps.
9. `DevRankUG` produces deterministic INDEX rankings over the approved pool.
10. At least one direct METRIC leaderboard and one TREND leaderboard are generated from observed data.
11. A public preview can be browsed before quarter close only through a distinct **PROVISIONAL** ranking state/surface and is explicitly labelled non-official.
12. The official 2026-Q3 snapshot is not frozen before the quarter ends.
13. The official 2026-Q3 data cutoff is **2026-09-30 23:59:59 Africa/Kampala** (`2026-09-30T20:59:59Z`).
14. The official 2026-Q3 snapshot is published only after eligibility, anomaly, provenance, and algorithm-version validation pass.
15. The website exposes Top 10 by default and only 20/30/50 as expansion options.
16. Public profiles expose methodology, evidence/provenance links where safe, ranking history, factor coverage, and algorithm version.
17. Share cards derive rank/score only from immutable published ranking-result IDs.
18. Failed publication attempts leave the previously official snapshot untouched.
19. The production deployment can be recreated from documented infrastructure/configuration steps.

## 4. Deployment architecture

### 4.1 Topology

```text
                         TOPTENUG PUBLIC
                              │
                    Next.js on Vercel
                              │
                         HTTPS / REST
                              │
                  FastAPI Core on Cloud Run
                              │
              ┌───────────────┴───────────────┐
              │                               │
        Public read path               Operations path
              │                               │
              │                       Cloud Run Jobs
              │                    discover / ingest
              │                    derive / validate
              │                         publish
              │                               │
              └───────────────┬───────────────┘
                              │
                    Supabase PostgreSQL
                         + pgvector
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
       Entity              Evidence            Observation
       graph              provenance            history
         │                    │                    │
         └────────────────────┼────────────────────┘
                              ↓
                     Derived metric layer
                              ↓
                    TopTenUG Ranking Engine
                         DevRankUG v1.x
                              ↓
                  Immutable quarterly snapshot
```

### 4.2 Vercel responsibilities

Vercel serves only the public Next.js application.

Responsibilities:

- render homepage/category/leaderboard/profile/methodology/share experiences;
- call the public FastAPI service over HTTPS;
- host OpenGraph/share-card routes that consume canonical published metadata;
- provide preview deployments for pull requests when useful;
- expose only non-secret public configuration such as `NEXT_PUBLIC_API_BASE_URL`.

Vercel must not receive a production database service-role credential. The browser and Next.js app do not calculate official ranks.

### 4.3 Cloud Run service responsibilities

The FastAPI Cloud Run service provides:

- public published ranking reads;
- explicitly separate provisional-preview reads;
- dashboard/category/profile/history/methodology APIs;
- canonical share metadata;
- health/readiness endpoints;
- future authenticated correction/admin endpoints through a separate protected surface.

The service is stateless. Durable state belongs in PostgreSQL.

### 4.4 Cloud Run Jobs responsibilities

Jobs invoke existing CLI/service-layer logic rather than duplicating ranking logic.

Initial production jobs:

- `toptenug-discover-technology`
- `toptenug-ingest-github`
- `toptenug-derive-quarter`
- `toptenug-validate-quarter`
- `toptenug-publish-quarter`

Cloud Scheduler may trigger recurrent discovery/ingestion jobs. Official publication remains explicitly gated and should not be blindly auto-published on a timer.

## 5. Environment model

Three logical environments are sufficient:

### 5.1 Local

- Docker PostgreSQL/pgvector or developer Supabase database.
- local Next.js/FastAPI.
- optional fixture-mode Gemini/GitHub clients.
- `.env` ignored; `.env.example` contains names only, never usable secrets.

### 5.2 Preview/Staging

- Vercel preview deployment.
- staging Cloud Run service/jobs.
- staging Supabase project or isolated staging project/schema.
- non-production Gemini/GitHub credentials where possible.
- may create `PROVISIONAL` ranking runs, never production `PUBLISHED` snapshots.

### 5.3 Production

- Vercel production domain.
- production Cloud Run service/jobs.
- production Supabase database.
- production secrets in managed secret stores.
- only validated official `PUBLISHED` ranking runs are exposed as official rankings.
- `PROVISIONAL` results, when exposed, are visually and API-level distinct from official results.

## 6. Database connectivity

### 6.1 Public API connection

The horizontally scalable Cloud Run API should use the Supabase connection pooler rather than creating uncontrolled long-lived direct database connections.

### 6.2 Administrative/migration connection

Migrations and controlled administrative jobs may use the direct database connection when required by PostgreSQL/Alembic behavior.

### 6.3 Vercel

The public web app calls FastAPI and does not connect directly to production PostgreSQL.

### 6.4 Vector support

`pgvector` is enabled during Phase 2 so the schema is ready for future semantic evidence search, but semantic search is not required to publish the first GitHub Developers ranking.

## 7. Secrets and security

### 7.1 Required runtime secrets/configuration

Backend/job configuration includes, as required:

- `DATABASE_URL`
- optional direct migration database URL
- `GITHUB_TOKEN`
- Gemini/Google AI credential or project configuration
- Gemini model configuration
- `TOPTENUG_PUBLIC_BASE_URL`
- CORS/public-origin configuration

Vercel public configuration includes:

- `NEXT_PUBLIC_API_BASE_URL`

### 7.2 Secret handling

- No credential values are committed to Git.
- Cloud Run runtime secrets use Google Secret Manager references where applicable.
- Vercel-managed environment variables hold only Vercel-side configuration required by the web deployment.
- GitHub Actions receive secrets only when a deployment workflow genuinely requires them.
- Production credentials are never copied into tests or sample files.
- Any future secret-scanner alert is treated as a credential incident until proven otherwise.

### 7.3 Database access

- Production database is not exposed through the public web client.
- Service-role/database credentials stay server-side.
- Read APIs expose curated public fields only.
- Evidence records may carry internal review metadata that is never automatically public.

## 8. Candidate discovery strategy

Discovery is intentionally broad; eligibility is intentionally conservative.

### 8.1 Discovery inputs

Phase 2 may discover candidates through:

- GitHub public profiles and repository/activity metadata;
- Google Search grounding via Gemini;
- first-party personal websites;
- public university/company/community pages;
- public conference/speaker pages;
- public developer-community lists;
- manually supplied seed candidates;
- other reputable public sources permitted by their terms.

Discovery ordering has no ranking value.

### 8.2 Candidate staging

Every discovered candidate enters a staging/review state before official eligibility.

Candidate record captures:

- display name;
- candidate GitHub identity;
- candidate first-party/public profile URLs;
- proposed Uganda relationship;
- supporting evidence IDs/URLs;
- confidence;
- review status;
- discovery source and timestamp.

Gemini output alone is never sufficient evidence.

### 8.3 Discovery and launch pool

The first live data campaign targets at least **100 plausible candidates**. The first official national Top 50 requires at least **50 approved, category-eligible candidates**.

A provisional preview may operate with a smaller reviewed pool if the UI clearly displays the pool size and the fact that discovery/review is still in progress.

Even 100 discovered candidates is not proof that the Uganda developer universe is exhaustive. The methodology page must disclose discovery coverage and candidate-universe limitations.

## 9. Uganda eligibility for the live ranking

Eligibility is a gate, not a score factor.

For the first GitHub Developers category, eligible people must have evidence supporting one of the approved person relationships:

- `UGANDAN_IN_UGANDA`
- `UGANDAN_DIASPORA`

`UGANDA_BASED_NON_UGANDAN` is excluded from the official **Ugandan GitHub Developers** category. If TopTenUG later creates a separately named **Uganda-based GitHub Developers** category, that category may define a different eligibility policy.

Additional category requirements for the first official list:

- resolvable public GitHub identity;
- evidence-backed eligible Uganda relationship;
- sufficient hard-metric observations to satisfy the published factor-coverage threshold;
- no unresolved duplicate/entity conflict;
- no unresolved anomaly that blocks publication.

Ambiguous nationality/residency evidence remains `REVIEW_REQUIRED` and cannot enter the official pool. Names, appearance, language, or an LLM guess are never sufficient to establish eligibility.

## 10. Evidence hierarchy

The existing hierarchy remains authoritative:

### Level A — authoritative structured source

Examples: GitHub API for GitHub metrics; official registries/datasets where relevant.

### Level B — first-party evidence

Personal site, official organization profile, official university profile, verified public account/profile.

### Level C — reputable third-party evidence

Recognized publication, conference, institution, industry database.

### Level D — other public web evidence

Useful for discovery or corroboration, with lower reliability.

### Level E — AI inference

Never accepted as standalone evidence.

Eligibility approval should normally require at least one strong first-party/reputable source or multiple mutually consistent independent public sources, subject to manual review.

## 11. GitHub hard-metric ingestion

The first live ranking should rely on GitHub metrics that TopTenUG can reproduce from source data.

Current metric family includes:

- `github.followers`
- `github.owned_repo_stars`
- `github.active_owned_repos_180d`
- `github.contributions_90d`
- `github.prs_and_reviews_90d`

Rules:

- forks are excluded from owned-project star/adoption metrics;
- time-window metrics use explicit observation cutoffs;
- each observation records source URL, source record identity where possible, observed timestamp, evidence ID, and raw value;
- repeated runs append/reconcile observations idempotently rather than rewriting historical truth;
- missing source data is represented as missing, not automatically zero;
- API errors/rate limits are recorded as ingestion failures, not ranking values.

## 12. Ranking model in production

### 12.1 Ranking families

The first live category demonstrates all three public ranking types:

- **METRIC:** a direct observable leaderboard such as GitHub followers or owned-repository stars.
- **INDEX:** `DevRankUG`, a versioned TopTenUG-owned composite.
- **TREND:** growth/change based on two valid observation windows/snapshots.

### 12.2 DevRankUG

The production algorithm definition remains versioned configuration/code. Any material factor, weight, normalization, missing-data, or eligibility-policy change increments the algorithm version and changelog.

Published ranking results persist:

- algorithm name/version;
- quarter;
- score;
- rank;
- factor breakdown;
- factor coverage;
- confidence/quality metadata;
- provenance references;
- publication timestamp.

### 12.3 AI isolation

The ranking package must continue to have no dependency on Gemini, search APIs, prompt output, or LLM client libraries.

### 12.4 Provisional rankings

Phase 2 introduces a distinct `PROVISIONAL` ranking-run state for preview calculations.

Rules:

- `PROVISIONAL` is never treated as `PUBLISHED`.
- Official ranking endpoints continue to return only `PUBLISHED` runs.
- Preview endpoints/routes must be visibly and structurally separate.
- Provisional results may change as discovery, evidence review, or observations change.
- Official share-card styling/badges are unavailable to provisional results.
- Conversion to an official snapshot is not an in-place status flip that mutates history; official publication creates/finalizes an auditable immutable published run after validation.

## 13. 2026-Q3 timeline and freeze semantics

Today is 2026-09-26, so Q3 is still open.

### 13.1 Before quarter close

Through 2026-09-30:

- discover candidates;
- verify identity and Uganda eligibility;
- ingest GitHub observations;
- run provisional calculations;
- test production deployment;
- expose a public preview only through the clearly labelled `PROVISIONAL` surface.

### 13.2 Official cutoff

The official Q3 evidence/observation cutoff is:

`2026-09-30 23:59:59 Africa/Kampala`

Equivalent UTC cutoff:

`2026-09-30T20:59:59Z`

No evidence first observed after that cutoff may be used to backfill an official Q3 metric unless the underlying source record itself is timestamped within the eligible window and the methodology explicitly permits late verification. Such late verification must be auditable.

### 13.3 Publish window

After cutoff:

1. freeze eligible Q3 observations;
2. complete identity/eligibility review;
3. derive metrics;
4. run anomaly checks;
5. validate coverage/provenance;
6. execute deterministic ranking;
7. review the proposed Top 50;
8. publish the immutable official run;
9. generate share cards/public report.

A practical publication target is early October 2026 after validation, not September 26.

## 14. Public product behavior

### 14.1 Homepage

The public homepage remains discovery-oriented rather than a raw admin dashboard.

It should show:

- TopTenUG identity/tagline;
- current official quarter;
- Technology/GitHub featured ranking;
- national digital pulse summary;
- movers/new entrants once historical data exists;
- category cards for future universes marked appropriately;
- methodology/transparency entry point.

Before the first official Q3 release, any live-data preview must carry an obvious **Provisional / not official** banner and reviewed-pool count.

### 14.2 Leaderboard

Default: Top 10.

Allowed expansion only:

- 10
- 20
- 30
- 50

Each result should expose enough context to understand the ranking without exposing internal/private review notes.

### 14.3 Profiles

Public profile pages may show:

- current official ranks;
- prior-quarter movement;
- score/rank history;
- factor breakdown;
- algorithm version;
- factor coverage/confidence;
- public evidence/source links;
- notable repositories/metrics where supported.

### 14.4 Share cards

Official visual cards are generated only from immutable `PUBLISHED` ranking-result IDs. Arbitrary query-string rank/score overrides are ignored. Provisional results do not receive official card treatment.

## 15. Review/admin workflow

Phase 2 requires a minimal operator workflow even if a polished admin console is deferred.

Operators need a way to inspect:

- staged candidate proposals;
- possible duplicate identities;
- Uganda eligibility evidence;
- conflicting evidence;
- source failures/rate limits;
- anomaly flags;
- candidates below coverage thresholds;
- proposed ranking output before publication.

The initial operator surface may be CLI + SQL/admin tooling + structured reports. A dedicated admin web console is a follow-on unless needed to make the launch safe.

## 16. Scheduling strategy

Scheduling must support fresh inputs without silently changing the official ranking.

Initial cadence:

- candidate discovery: weekly;
- GitHub metric ingestion: daily or several times per week depending on quota/cost;
- provisional derivation: weekly;
- validation: manually triggered during quarter-close preparation;
- official publication: manually authorized after cutoff and review.

Cloud Scheduler triggers Cloud Run Jobs. Scheduler configuration contains no ranking formula or decision logic.

## 17. Reliability and idempotency

Every job must be safe to retry.

Requirements:

- source-record uniqueness/idempotency keys prevent duplicate observations where appropriate;
- ingestion runs record start/end/status/counts/error category;
- ranking runs record algorithm version, cutoff, candidate counts, validation status, and publication status;
- failed jobs do not partially mutate an official snapshot;
- publication is atomic from the public reader's perspective;
- prior official snapshots remain readable and immutable.

## 18. Observability

Minimum production observability:

- Cloud Run service/job logs;
- structured job/run IDs in logs;
- ingestion/ranking run status in PostgreSQL;
- counts for discovered, reviewed, eligible, ingested, ranked and published entities;
- source error/rate-limit counts;
- API health/readiness endpoint;
- deployment version/commit SHA visible in diagnostics.

Alerting can start lightweight. The system should favor actionable run failures rather than high-volume notification noise.

## 19. CI/CD policy

The CI-noise fix from the MVP remains in force.

Full code CI runs on:

- pull requests targeting `main`;
- pushes to `main`;
- manual `workflow_dispatch` when deliberately requested.

Feature-branch pushes do not run the entire release suite automatically.

Docs-only changes skip code CI.

Superseded runs cancel in progress.

Production deployment should be a separate workflow from test CI. It should deploy only from an approved main commit or a deliberate manual release action, not from every feature commit.

## 20. Deployment workflow

### 20.1 Vercel

- repository project rooted at `apps/web`;
- preview deployments available for PR review;
- production deployment follows merge/release policy;
- `NEXT_PUBLIC_API_BASE_URL` targets the correct environment API.

### 20.2 Cloud Run API

- build `infra/cloudrun/core.Dockerfile`;
- deploy immutable revision tagged/labelled with Git commit SHA;
- configure managed secrets and environment;
- restrict CORS to intended public origins while preserving documented API use.

### 20.3 Cloud Run Jobs

- build/deploy worker image from `infra/cloudrun/worker.Dockerfile`;
- create explicit job definitions for discovery/ingestion/derive/validate/publish;
- supply command arguments per job rather than baking quarter/category into the image;
- use least-privilege service accounts.

### 20.4 Supabase

- create production project/database;
- enable required extensions;
- run Alembic migration round-trip in staging, then upgrade production;
- use pooled connection for scalable API traffic;
- document backup/restore expectations before official publication.

## 21. Real-data launch workflow

### Stage A — infrastructure

1. provision Supabase database;
2. deploy staging API/jobs;
3. deploy Vercel preview/staging frontend;
4. verify health, CORS and DB connectivity;
5. verify secrets are not present in repository/build logs.

### Stage B — candidate discovery

1. seed known Uganda developer candidates;
2. run Gemini/Search-assisted discovery;
3. deduplicate identities;
4. collect evidence;
5. place ambiguous candidates in manual review;
6. continue discovery until the launch-pool threshold is satisfied.

### Stage C — hard metrics

1. ingest GitHub data for reviewed candidates;
2. verify provenance and idempotency;
3. rerun to prove no accidental duplicate inflation;
4. inspect missing/rate-limited profiles.

### Stage D — provisional ranking

1. derive metrics;
2. create `PROVISIONAL` METRIC/INDEX/TREND outputs;
3. inspect factors/coverage/anomalies;
4. verify discovery order does not affect ranking order;
5. expose preview only with provisional labelling and pool-size disclosure.

### Stage E — quarter close

After 2026-09-30 cutoff:

1. freeze Q3 observations;
2. finish eligibility review;
3. validate;
4. publish official run;
5. verify API/web/share surfaces against published IDs;
6. capture release report and methodology version.

## 22. Error handling

### Source unavailable/rate-limited

- preserve prior observations;
- record typed source error;
- retry according to source policy;
- do not substitute AI-estimated metrics.

### Candidate identity ambiguous

- keep staged/review-required;
- do not merge identities automatically when evidence is conflicting.

### Uganda relationship ambiguous

- candidate is not official-ranking eligible until resolved.

### Low factor coverage

- calculate diagnostic score if useful, but mark unqualified and prevent official publication when below category threshold.

### Validation failure

- do not publish;
- preserve prior official snapshot;
- correct evidence/data/config and retry in a new auditable run.

### Deployment failure

- prior Cloud Run/Vercel production revision remains the rollback target;
- database migrations must be backward-safe within the release procedure or explicitly gated before deployment.

## 23. Testing requirements

### Unit

- source adapters;
- evidence/eligibility rules;
- deterministic METRIC/INDEX/TREND ranking;
- missing-data policy;
- anomaly/coverage rules;
- provisional-vs-published isolation;
- share-card canonical metadata.

### Integration

- Supabase-compatible PostgreSQL migrations;
- SQL-backed public API reads;
- source → evidence → observation → metrics → ranking flow;
- Cloud Run CLI/job commands using fixture clients.

### E2E

- Vercel/Next.js against staging FastAPI;
- Top 10/20/30/50 only;
- profile/methodology navigation;
- share-card canonicality;
- provisional vs official labelling;
- responsive desktop/mobile behavior.

### Production smoke

After deployment:

- `/health` succeeds;
- database connection succeeds;
- official/public ranking endpoints return only `PUBLISHED` results;
- preview endpoints never masquerade as official;
- first production discovery job records a run;
- first GitHub ingestion job persists provenance-backed observations;
- no external source can write official rank fields.

## 24. Privacy, ethics and source policy

- public information only;
- no leaked/private/sensitive personal data;
- honor source terms and access restrictions;
- prefer APIs and first-party sources;
- do not scrape authenticated/private surfaces;
- do not infer protected/sensitive traits;
- do not infer Uganda eligibility from names, appearance, language, or model intuition;
- make evidence-backed corrections possible;
- document candidate-universe limitations;
- never present an incomplete discovery universe as exhaustive Uganda-wide truth without qualification.

## 25. Cost controls

Phase 2 should remain hobby-project-friendly.

Controls:

- Vercel deployment sized for public preview traffic;
- Cloud Run scales to zero where applicable;
- jobs run on explicit schedules rather than continuous workers;
- Supabase selected for managed Postgres without an always-on Cloud SQL requirement;
- cache/reuse evidence where safe;
- avoid repeated Gemini research when evidence has not materially changed;
- batch GitHub ingestion and respect rate limits;
- store raw evidence/observations once and recompute derived metrics locally.

## 26. Explicit non-goals for Phase 2

Not required before the first real GitHub Developers public release:

- Media/TV/Radio rankings;
- creator/social rankings;
- startup rankings;
- research rankings;
- MCP server;
- A2A multi-agent orchestration;
- public Ranking Lab;
- a full admin dashboard;
- automated ranking appeals;
- universal cross-category `Top Ugandan` score;
- live official rank changes between quarterly snapshots.

## 27. Follow-on sequence

After the first real GitHub Developers release:

1. AI/Data subcategory using the same person/entity foundation;
2. broader Technology builder categories;
3. Startups & Digital Economy;
4. Creators & Social;
5. Media (TV/Radio/News/Podcast);
6. Research & Knowledge;
7. semantic evidence search;
8. MCP read surface;
9. A2A research orchestration;
10. Ranking Lab simulations.

Each substantial new universe gets its own design/plan because its evidence and ranking semantics differ.

## 28. Architectural invariants

```text
Vercel serves the public Next.js experience.
Cloud Run serves the stateless FastAPI API.
Cloud Run Jobs perform long-running operational work.
Supabase PostgreSQL stores canonical entities, evidence, observations and snapshots.
Google/Gemini assists discovery, extraction, grounding and verification.
GitHub supplies hard GitHub metrics.
TopTenUG-owned deterministic code computes every official score/rank.
Eligibility is evidence-backed and separate from ranking strength.
PROVISIONAL and PUBLISHED ranking runs are structurally distinct.
Official rankings are immutable quarterly snapshots.
Q3 2026 cannot be officially frozen before 2026-09-30 23:59:59 Africa/Kampala.
The public interface defaults to Top 10 and never expands beyond 50.
Production secrets never live in Git.
Failed publication never replaces the prior official snapshot.
```

## 29. Implementation boundary

This design intentionally decides the system boundaries and rollout semantics but does not yet prescribe every command/file change. The implementation plan must specify:

- exact Supabase project/schema/migration setup;
- Vercel project/environment configuration;
- Cloud Run API/job deployment definitions;
- secret/IAM setup;
- production/staging configuration loading;
- `PROVISIONAL` ranking persistence/API behavior;
- candidate discovery adapters/prompts/grounding rules;
- review-state persistence/operator workflow;
- production GitHub ingestion batching;
- deployment workflows and smoke tests;
- real-data launch checklist for 2026-Q3.
