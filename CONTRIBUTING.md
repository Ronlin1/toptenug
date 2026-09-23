# Contributing to TopTenUG 🇺🇬

Thanks for helping build TopTenUG.

TopTenUG is an open, evidence-driven ranking and discovery platform for Uganda's digital ecosystem. Contributions are welcome across engineering, data, AI/ML, research, design, methodology, documentation, and ecosystem knowledge.

## Before contributing

Please keep these project principles in mind:

1. **Rank evidence, not reputation.** Rankings must be grounded in public, reviewable evidence.
2. **AI does not choose winners.** AI may discover, classify, extract, reconcile, verify, and explain evidence; deterministic TopTenUG logic produces official rankings.
3. **Prefer authoritative sources.** Structured first-party or official APIs should be used when available.
4. **Preserve provenance.** New metrics and observations should retain their source, retrieval time, and methodology.
5. **Respect access rules and privacy.** Do not contribute private, leaked, paywalled, or improperly obtained personal data. Scraping work must respect applicable terms, robots/access controls, rate limits, and legal/ethical constraints.
6. **Avoid popularity-only assumptions.** Large follower counts, search visibility, or media mentions are signals, not automatic proof of impact.
7. **Keep ranking methodology inspectable.** New indexes should document eligibility, inputs, normalization, weighting, confidence, and known limitations.
8. **Top 10 is the public default.** Leaderboards may expand to 50 maximum.
9. **Quarterly snapshots are official.** Continuous/provisional data must not silently replace an official quarterly snapshot.
10. **Be respectful and evidence-focused.** Ranking people and organizations can be sensitive; critiques should focus on data, methodology, implementation, and reproducibility.

## Ways to contribute

### Data sources

Suggest or implement reliable public sources for categories such as:

- GitHub and open source;
- YouTube and other public social metrics;
- startups and products;
- television, radio, news, and podcasts;
- research and publications;
- communities and events;
- companies, universities, and digital services;
- public datasets and open government data.

A good data-source proposal explains:

- what it measures;
- whether an official API exists;
- geographic/identity coverage;
- expected update frequency;
- rate limits/costs;
- licensing or terms considerations;
- known biases or blind spots.

### Ranking algorithms

Ranking proposals should include:

- category and ranking type (`METRIC`, `INDEX`, or `TREND`);
- eligibility rules;
- candidate universe;
- raw metrics;
- normalization method;
- weights or formula;
- time decay/freshness rules;
- missing-data handling;
- anomaly or manipulation handling;
- confidence treatment;
- validation approach;
- explainability plan;
- versioning impact.

Avoid proposing a single opaque AI prompt as an official ranking algorithm.

### AI / Gemini

Useful contribution areas include:

- grounded candidate discovery;
- structured extraction;
- entity matching suggestions;
- classification;
- anomaly investigation;
- evidence summarization;
- semantic retrieval;
- ranking explanations;
- MCP tools;
- A2A agent workflows.

All important AI outputs should be traceable to evidence and validated before they influence official data.

### Frontend and visualization

TopTenUG aims for a hybrid experience: a premium, highly shareable public interface with deeper analytics available on demand.

Useful contributions include:

- category cards;
- leaderboard interactions;
- profile pages;
- rank-history charts;
- score-breakdown visualizations;
- Uganda ecosystem maps;
- mobile UX;
- accessibility;
- downloadable/shareable ranking cards;
- social/OpenGraph previews.

### Documentation and research

Contributions that improve methodology, taxonomy, source documentation, bias analysis, or reproducibility are as important as code.

## Development workflow

The implementation plan has not yet been finalized. Until the architecture spec is approved, please avoid large implementation PRs that make irreversible stack decisions.

For now:

1. Open an issue describing the proposed contribution.
2. Link sources/evidence where relevant.
3. Keep the scope focused.
4. For methodology changes, explain how historical rankings would be affected.
5. For implementation changes, include tests once the technical stack is established.

## Pull requests

A good pull request should:

- explain the problem and proposed solution;
- link the relevant issue;
- avoid unrelated refactoring;
- include tests for behavior changes once implementation begins;
- document new data sources or ranking rules;
- preserve provenance and reproducibility;
- update user-facing or methodology docs when behavior changes.

## Data corrections and appeals

If you believe a TopTenUG record, identity match, metric, or ranking input is incorrect, open a data-correction issue with public supporting evidence. Corrections should update the evidence layer first; ranking outputs should then be recomputed from the corrected data rather than manually edited.

## Ranking methodology changes

Official ranking algorithms are versioned. A methodology change should never be silently applied to historical or current published snapshots.

Material changes should document:

- previous version;
- new version;
- reason for change;
- expected ranking impact;
- validation results;
- first quarter using the new version.

## Community conduct

Be constructive, respectful, and precise. TopTenUG may represent real people and organizations, so avoid harassment, unsupported allegations, discriminatory ranking criteria, or invasive personal data.

## Questions

Open a GitHub issue if you are unsure whether an idea belongs in the project. Early discussion is encouraged, especially for new ranking categories, data sources, and methodology changes.
