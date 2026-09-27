# TopTenUG Live-Data Review Procedure

The first live ranking is **Technology → GitHub Developers → Uganda**. This procedure is deliberately human-gated: discovery systems may propose candidates, but they never approve eligibility or assign official rank.

## Core rule

> Google/Gemini/Search and source APIs provide evidence and measurements. TopTenUG reviewers decide eligibility from evidence, and TopTenUG-owned deterministic algorithms calculate rank.

Do not approve a candidate from a name, appearance, language, model guess, search ordering, or an unsupported profile claim.

## 1. Discover and stage candidates

Run grounded discovery and persist proposals:

```bash
toptenug discover --universe technology --persist
```

Discovery should continue until at least 100 plausible Uganda-linked GitHub developer candidates exist before claiming a national first release. Discovery count is not ranking strength and does not imply the candidate universe is exhaustive.

## 2. Review evidence

List unresolved proposals:

```bash
toptenug review list --status REVIEW_REQUIRED
```

For each candidate, verify:

- the public GitHub identity resolves to the intended person;
- Uganda relationship evidence supports either `UGANDAN_IN_UGANDA` or `UGANDAN_DIASPORA`;
- supporting URLs are public and appropriate to retain as evidence;
- conflicting same-name or duplicate identities are resolved before approval.

Approval requires an explicit reviewer note:

```bash
toptenug review approve \
  --candidate <uuid> \
  --relation UGANDAN_IN_UGANDA \
  --note "Evidence reviewed: ..."
```

Reject unsupported or incorrect proposals explicitly:

```bash
toptenug review reject --candidate <uuid> --note "Reason and evidence reviewed"
```

The first official `Ugandan GitHub Developers` category excludes `UGANDA_BASED_NON_UGANDAN`. A future separately named Uganda-based category may use a different policy.

## 3. Resolve duplicates conservatively

Candidates with the same normalized name but conflicting identities remain review-required. Do not merge two people merely because their names match. Confirm GitHub identity and corroborating public evidence first.

An unresolved duplicate conflict is a national-release blocker.

## 4. Ingest GitHub hard metrics

After review, ingest approved candidates in controlled batches:

```bash
toptenug ingest github-batch --limit 25
```

A source failure must not be converted into zero or AI-estimated metrics. Inspect partial/failed ingestion runs, retry recoverable failures, and preserve prior valid observations.

Only the latest GitHub ingestion run is used by launch readiness for current source-failure status; a recovered historical incident does not permanently block launch.

## 5. Derive and preview

Derive the quarter using the shared Africa/Kampala quarter window:

```bash
toptenug derive --quarter 2026-Q3
```

Create a provisional run:

```bash
toptenug preview --category github-developers --quarter 2026-Q3
```

`PROVISIONAL` is not official. It may change as discovery, review, and source observations change. Official share-card treatment is unavailable to provisional rows.

## 6. Check launch readiness

Run:

```bash
toptenug report launch-readiness \
  --category github-developers \
  --quarter 2026-Q3
```

The national-release gate requires all of the following:

- at least 100 discovered candidates;
- at least 50 approved category-eligible developers;
- at least 50 approved eligible developers with resolved GitHub identities;
- at least 50 qualified ranking rows;
- zero unresolved duplicate conflicts;
- zero blocking ranking anomalies;
- zero failures in the latest GitHub ingestion run;
- ranking validation passes.

A smaller reviewed pool may be `preview_ready=true` when it has eligible and qualified candidates, ranking validation passes, and a valid provisional run exists. That does **not** make it ready for a national official release.

## 7. Q3 publication gate

The 2026-Q3 exclusive cutoff is:

```text
2026-09-30T21:00:00Z
```

which is midnight after September 30 in Africa/Kampala. `publish` must reject any clock before that boundary.

After cutoff, rerun derivation, validation, readiness, and human review. Official publication remains a deliberate operator action; it is never automatically approved by discovery, Gemini, Scheduler, or a readiness report.

## 8. Corrections and disputes

If evidence is wrong or incomplete:

- correct the evidence/candidate record;
- rerun the affected ingestion/derivation/validation stages;
- never edit a published rank directly;
- never mutate an immutable official snapshot to hide a prior result;
- record methodology or algorithm-version changes explicitly.
