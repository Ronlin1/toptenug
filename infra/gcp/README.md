# Google Cloud deployment for TopTenUG Phase 2

Region: `europe-west3` (Frankfurt). Build images from the checked-in Dockerfiles and pin every deployed revision/job image to the Git commit SHA.

## Runtime identities

Use distinct least-privilege identities where practical:

- API runtime: read/write database access through managed `DATABASE_URL`; read only the secrets needed by FastAPI.
- Worker runtime: database/source credentials needed by the specific operational jobs.
- Scheduler invoker: permission to invoke configured Cloud Run Jobs only; it does not receive ranking/database credentials.

Runtime secret values belong in Secret Manager and are referenced by Cloud Run. Do not put secret values in checked-in env files or command logs.

## Images

```bash
GCP_IMAGE_ROOT="${TOPTENUG_GCP_REGION}-docker.pkg.dev/${TOPTENUG_GCP_PROJECT_ID}/${TOPTENUG_ARTIFACT_REPOSITORY}"

gcloud builds submit . \
  --tag "${GCP_IMAGE_ROOT}/core:${TOPTENUG_COMMIT_SHA}" \
  --file infra/cloudrun/core.Dockerfile

gcloud builds submit . \
  --tag "${GCP_IMAGE_ROOT}/worker:${TOPTENUG_COMMIT_SHA}" \
  --file infra/cloudrun/worker.Dockerfile
```

If the installed `gcloud builds submit` version does not accept `--file`, build through Docker/Cloud Build config instead; keep the two checked-in Dockerfiles authoritative.

## API service

Service name: `toptenug-core`.

Deploy the core image in `europe-west3`; configure non-secret environment values and Secret Manager references separately. `DATABASE_URL` is the Supabase transaction-pooler URL. Migrations never run through the public API service and never use that pooler URL.

## Worker jobs

All jobs use the same worker image and differ only by arguments:

```text
toptenug-discover-technology  → discover --universe technology --persist
toptenug-ingest-github        → ingest github-batch --limit 100
toptenug-derive-quarter       → derive --quarter 2026-Q3
toptenug-validate-quarter     → validate --category github-developers --quarter 2026-Q3
toptenug-publish-quarter      → publish --category github-developers --quarter 2026-Q3
```

Publication is deliberately manual. The `toptenug-publish-quarter` job may exist, but Cloud Scheduler must never create an automatic production schedule for it.

## Scheduler

Initial recurring triggers:

- discovery: weekly;
- GitHub ingestion: daily;
- provisional derive/preview preparation: weekly;
- validate: manual during quarter-close preparation;
- publish: manual only after human review and the quarter cutoff.

Scheduler configuration only invokes jobs. It contains no ranking formula, eligibility rule, or publication decision.

## Pre-deploy validation

Before creating/updating services or jobs:

```bash
python scripts/validate_deployment_config.py --environment staging
```

The validator prints only a redacted summary and rejects region drift, DB role confusion, preview/production API aliasing, and Vercel API misrouting.
