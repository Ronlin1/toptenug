# Supabase for TopTenUG Phase 2

TopTenUG uses Supabase only as the managed PostgreSQL/pgvector data layer. The public Vercel application never receives a database credential.

## Region

Provision the first staging/production projects in `eu-central-1` (Frankfurt). Cloud Run is paired in `europe-west3` (Frankfurt). If either region is unavailable, stop and record an explicit region-change decision before provisioning the other side.

## Connections

Copy connection values from the Supabase **Connect** panel; do not construct pooler hostnames from the region.

Use two distinct URLs:

- `DATABASE_URL`: transaction-pooler connection for the horizontally scalable Cloud Run API/jobs. The TopTenUG runtime engine disables Psycopg automatic prepared statements for this connection.
- `DATABASE_ADMIN_URL`: direct PostgreSQL connection for Alembic migrations and controlled administration. Never point this at the transaction pooler.

The Phase 2 validator expects the runtime pooler to be distinguishable from the direct admin endpoint and rejects accidental reuse.

## Extensions and migrations

Enable `vector`, then run migrations with the direct admin URL from an environment that can reach the direct database endpoint:

```bash
export DATABASE_URL='<transaction-pooler-url>'
export DATABASE_ADMIN_URL='<direct-admin-url>'
cd services/core
uv run alembic upgrade head
```

Before production publication, verify a staging migration round trip against the intended schema and confirm backup/restore expectations in the deployment record.

## Secrets

Do not commit connection strings, passwords, project service-role keys, or copied Connect-panel output. Repository examples contain variable names only.
