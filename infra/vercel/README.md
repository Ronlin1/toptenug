# Vercel deployment for TopTenUG web

Create a Vercel project named `toptenug-web` with repository root directory `apps/web`.

## Environment separation

Set `NEXT_PUBLIC_API_BASE_URL` independently by Vercel environment:

- Preview → staging Cloud Run API URL.
- Production → production Cloud Run API URL.

When a live provisional preview is intentionally enabled, also set:

```text
NEXT_PUBLIC_ENABLE_PROVISIONAL_PREVIEW=true
NEXT_PUBLIC_PREVIEW_QUARTER=2026-Q3
```

Production can leave preview mode disabled until explicitly approved. The app never infers provisional mode from a missing official ranking.

## Security boundary

Do not add `DATABASE_URL`, `DATABASE_ADMIN_URL`, GitHub tokens, Gemini credentials, Supabase service-role keys, or Google Cloud service-account credentials to the web project. Vercel talks to the public FastAPI service over HTTPS.

## Verification

Before promoting a deployment, verify:

- `/technology/github-developers` has no horizontal overflow;
- only Top 10/20/30/50 controls appear;
- preview deployments show the non-official banner only when explicitly enabled;
- production/offical mode contains no provisional badge;
- provisional rows do not expose official share controls.
