# TopTenUG Quarterly Operations Runbook

Google Search, Gemini, GitHub, journals, datasets and crawled public pages provide evidence and metric inputs only. **They never assign an official TopTenUG rank.** Only the versioned deterministic TopTenUG ranking engine may calculate official scores/ranks.

Production secrets belong in Google Secret Manager: `DATABASE_URL`, `GITHUB_TOKEN`, `GEMINI_API_KEY`, `GEMINI_MODEL`, `TOPTENUG_PUBLIC_BASE_URL`.

Continuous work:
```bash
toptenug discover --universe technology
toptenug ingest github --entity <uuid>
toptenug derive --quarter 2026-Q3
```

Quarter close:
1. Freeze the observation cutoff.
2. Complete identity/Uganda eligibility review.
3. `toptenug derive --quarter 2026-Q3`
4. `toptenug validate --category github-developers --quarter 2026-Q3`
5. Review anomalies, provenance, coverage and algorithm version.
6. `toptenug publish --category github-developers --quarter 2026-Q3`

A failed run never replaces the previous official snapshot. Correct evidence/observations and retry; never manually edit `RankingResult.rank`. Algorithm changes create a new version, never mutate a published version.
