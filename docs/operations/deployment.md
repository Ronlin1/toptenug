# TopTenUG Hybrid Deployment Runbook

This runbook covers the Phase 2 production platform boundary:

- **Vercel** → public Next.js app (`apps/web`)
- **Google Cloud Run** → stateless FastAPI API
- **Cloud Run Jobs** → discovery/ingestion/derive/validate/publish operations
- **Supabase** → canonical PostgreSQL + pgvector
- **Google Secret Manager** → Cloud Run runtime secrets

External intelligence/source systems provide evidence and measurements only. Deployment configuration never contains ranking formulas. Official rank is still calculated only by TopTenUG-owned deterministic ranking code.

## 1. Region pair

Initial pair:

```text
Supabase: eu-central-1 (Frankfurt)
Cloud Run: europe-west3 (Frankfurt)
```

If either side cannot be provisioned there, stop and record a deliberate region decision before moving one side elsewhere.

## 2. Required variables

Names only; never commit values:

```text
TOPTENUG_GCP_PROJECT_ID
TOPTENUG_GCP_REGION=europe-west3
TOPTENUG_ARTIFACT_REPOSITORY
TOPTENUG_SUPABASE_REGION=eu-central-1
DATABASE_URL
DATABASE_ADMIN_URL
GITHUB_TOKEN
GEMINI_API_KEY
TOPTENUG_PUBLIC_BASE_URL
TOPTENUG_ALLOWED_ORIGINS
TOPTENUG_COMMIT_SHA
TOPTENUG_PREVIEW_API_BASE_URL
TOPTENUG_PRODUCTION_API_BASE_URL
NEXT_PUBLIC_API_BASE_URL
```

Validate before deployment:

```bash
python scripts/validate_deployment_config.py --environment staging
```

The output is intentionally redacted.

## 3. Database roles

`DATABASE_URL` is the Supabase transaction-pooler URL used by Cloud Run runtime traffic. TopTenUG disables Psycopg automatic prepared statements for this connection.

`DATABASE_ADMIN_URL` is the direct Supabase PostgreSQL connection for Alembic/admin work. The validator rejects a pooler URL in this role.

Run migrations from a controlled environment that can reach the direct connection:

```bash
cd services/core
DATABASE_URL="$DATABASE_ADMIN_URL" uv run alembic upgrade head
```

Do not silently fall back to the runtime pooler for migrations.

## 4. Build verification

Before external deployment:

```bash
docker build -f infra/cloudrun/core.Dockerfile -t toptenug-core:test .
docker build -f infra/cloudrun/worker.Dockerfile -t toptenug-worker:test .
```

Both images must build from repository root.

## 5. Cloud Run

Follow `infra/gcp/README.md`. Pin API revision and worker jobs to `TOPTENUG_COMMIT_SHA`. Runtime secrets come from Secret Manager references and should not be printed by deploy scripts/workflows.

The production publish job is never scheduled automatically.

## 6. Supabase

Follow `infra/supabase/README.md`. Enable `vector`, use Connect-panel URLs, and keep runtime/admin connections separate.

## 7. Vercel

Follow `infra/vercel/README.md`. Root directory is `apps/web`. Preview and Production `NEXT_PUBLIC_API_BASE_URL` values are separate. No DB or backend source credentials belong in Vercel.

## 8. Environment routing checks

For staging:

- Vercel Preview points only to staging Cloud Run;
- staging Cloud Run points only to staging Supabase;
- production API URL remains distinct.

For production:

- Vercel Production points only to production Cloud Run;
- production Cloud Run points only to production Supabase;
- migrations use production direct admin URL only during an explicit release operation.

## 9. Rollback

A failed application deployment rolls back to the previous Cloud Run/Vercel revision. A failed publication never replaces the prior `PUBLISHED` ranking snapshot. Database migrations must be verified in staging before production promotion.

## 10. Verification record

For every staging/production deployment record only non-secret identifiers:

- Git commit SHA;
- Vercel deployment/project identifier;
- Cloud Run service/job names and region;
- Supabase project reference and region;
- migration result;
- smoke-test result;
- deployment timestamp.

Never paste connection URLs, tokens, passwords or Secret Manager payloads into deployment records.
