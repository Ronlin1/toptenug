# TopTenUG Design Specification

**Date:** 2026-09-23  
**Status:** Proposed design for review  
**Project:** TopTenUG  
**Repository:** `Ronlin1/toptenug`

## 1. Product intent

TopTenUG is an open, Uganda-focused discovery, ranking, and digital-intelligence platform.

The product deliberately combines three goals:

1. **Technical depth** — demonstrate serious engineering across APIs, public data, web research, ingestion pipelines, entity resolution, AI/ML, ranking algorithms, historical data, MCP, A2A, search, and analytics.
2. **Credibility** — create transparent, evidence-driven, reproducible quarterly rankings that can mature into a useful Ugandan digital intelligence index.
3. **Viral public UX** — make rankings visually attractive, easy to explore, downloadable, and shareable enough that ranked people, organizations, and interested users want to distribute them.

The public promise is:

> **TopTenUG — Uganda, ranked by data.**

TopTenUG is not intended to be a generic directory, an opaque popularity contest, or an LLM-generated opinion about who is "best."

## 2. Success criteria

A successful TopTenUG should:

- publish useful Top 10 rankings across many Uganda-focused digital categories;
- allow each leaderboard to expand to 20, 30, or 50 entries, but never beyond 50 in the public ranking experience;
- distinguish direct metrics from composite indexes and trend rankings;
- explain how every official index was calculated;
- preserve raw observations and historical quarterly snapshots;
- link important claims and ranking inputs to public evidence;
- support rank history, score history, movers, new entrants, and streaks;
- create downloadable/shareable social cards from official results;
- expose useful programmatic interfaces through an API and later MCP/A2A integrations;
- remain extensible enough to add new categories without creating a separate ranking system for each one;
- be open to community contributions while protecting ranking integrity.

## 3. Product experience

### 3.1 Public homepage

The homepage should be visually simple and discovery-oriented rather than exposing the full complexity of the intelligence platform.

It should include:

- TopTenUG identity and current quarter;
- a national digital pulse summary;
- trending rankings;
- biggest movers;
- new entrants;
- category/universe cards;
- highlights from the current quarterly index;
- pathways to methodology and historical snapshots.

The visual direction is a **hybrid**: premium, clean, large-card discovery at the top level, with richer analytics and evidence views inside categories and profiles.

### 3.2 Category routes

A category card opens a category dashboard, not a single leaderboard.

Example:

```text
/media
  /television
  /radio
  /digital-news
  /podcasts
```

A category page may contain many logical leaderboards such as:

- Top Television Stations;
- Most Subscribed Television YouTube Channels;
- Fastest-Growing Radio Brands;
- Most Digitally Engaging Media Brands;
- Top Technology Publications.

### 3.3 Leaderboards

All public leaderboards default to 10 entries.

Users may switch to:

- Top 10;
- Top 20;
- Top 30;
- Top 50.

There is no public infinite ranking list.

A ranking row/card should be able to show:

- rank;
- movement from previous official quarter;
- entity name and image/logo where available;
- key metric or index score;
- ranking type (`METRIC`, `INDEX`, `TREND`);
- current quarter;
- evidence/source confidence where relevant;
- share action;
- link to profile and methodology.

### 3.4 Profiles

Profiles can represent people, companies, products, media entities, communities, repositories, publications, and other supported entities.

A profile may show:

- current rankings across categories;
- historical rank movements;
- historical score movements;
- public source accounts/identifiers;
- projects, publications, products, or organizations;
- ranking factor breakdowns;
- public evidence;
- confidence/coverage information;
- notable quarterly milestones.

## 4. Initial ranking universes

The top-level taxonomy should remain intentionally small while allowing many rankings beneath each universe.

### Technology & Builders

Examples: developers, software engineers, GitHub users, open-source contributors, AI/ML engineers, data scientists, data engineers, cloud engineers, DevOps engineers, cybersecurity professionals, backend developers, frontend developers, mobile developers, Web3 developers, database engineers, platform engineers, and emerging technology builders.

### Startups & Innovation

Examples: startups, founders, technical founders, emerging startups, fastest-growing startups, funded startups, bootstrapped startups, AI startups, fintech, agritech, healthtech, edtech, climate-tech, SaaS, mobility, logistics, e-commerce, developer tools, and creative technology.

### Social & Creators

Examples: LinkedIn, X, YouTube, TikTok, Instagram, creators, influencers, cross-platform creators, tech creators, educational creators, business creators, audience growth, engagement, reach, and consistency.

### Media

Examples: television stations, radio stations, newspapers, digital publishers, news platforms, podcasts, podcast hosts, streaming presence, subscriber counts, audience growth, social reach, and digital engagement.

### Digital Marketing

Examples: marketers, agencies, SEO specialists, social-media strategists, growth marketers, performance marketers, content marketers, brand strategists, influencer-marketing agencies, digital-first brands, and campaigns.

### Products & Tools

Examples: Ugandan-built applications, SaaS, APIs, AI tools, developer tools, open-source libraries, mobile apps, bots, MCP servers, AI agents, browser extensions, and platforms.

### Open Source

Examples: GitHub repositories, developers, organizations, stars, forks, contributors, maintainers, activity, adoption, project growth, and emerging repositories.

### Research & Knowledge

Examples: AI researchers, computing researchers, publications, citations, recent papers, universities, labs, open research, and research software.

### Communities & Events

Examples: developer communities, AI communities, student communities, university technology clubs, innovation hubs, conferences, hackathons, meetups, and ecosystem organizers.

### Education & Talent

Examples: universities, coding schools, bootcamps, student developers, student founders, university GitHub activity, startup activity, and research output.

### Companies & Digital Economy

Examples: software companies, IT firms, digital agencies, telecoms, ISPs, fintechs, e-commerce platforms, digital employers, and technology-enabled businesses.

### Quarterly Pulse

Examples: biggest movers, new Top 10 entrants, breakout developers, emerging creators, rising startups, trending repositories, new products, fast-growing media brands, and notable ecosystem shifts.

## 5. Generic entity model

TopTenUG should not build unrelated ranking systems for people, startups, radio stations, and repositories.

The platform uses a generic `Entity` abstraction with typed extensions.

Candidate entity types include:

```text
PERSON
STARTUP
COMPANY
PRODUCT
APP
REPOSITORY
ORGANIZATION
MEDIA_HOUSE
TV_STATION
RADIO_STATION
PODCAST
YOUTUBE_CHANNEL
UNIVERSITY
COMMUNITY
EVENT
PUBLICATION
AGENCY
TOOL
```

Each entity can have:

- canonical identity;
- aliases;
- public source identifiers;
- Uganda relationship/eligibility evidence;
- type-specific metadata;
- observations;
- evidence;
- derived metrics;
- ranking appearances;
- historical snapshots.

The model must support one real-world entity having multiple public identities without creating duplicate ranking candidates.

## 6. Uganda eligibility

Eligibility is a separate concern from ranking strength.

The system should support explicit relationship labels such as:

- Ugandan, currently in Uganda;
- Ugandan diaspora;
- Uganda-based non-Ugandan;
- Uganda-founded organization;
- Uganda-operating organization;
- Uganda-focused product/community/publication.

Every ranking category defines its eligibility policy. A candidate can be discoverable in TopTenUG without automatically being eligible for every leaderboard.

Eligibility evidence should be stored and reviewable.

## 7. Ranking taxonomy

Every leaderboard has one of three primary types.

### 7.1 METRIC

A ranking based directly on an observable public metric.

Examples:

- YouTube subscribers;
- GitHub stars;
- repository forks;
- publication citations;
- public follower counts where lawfully and reliably obtainable.

A metric ranking should avoid implying that the metric is equivalent to overall quality or impact.

### 7.2 INDEX

A TopTenUG-defined composite algorithm combining multiple normalized signals.

Example index families may include:

- `DevRankUG`;
- `CreatorRankUG`;
- `StartupRankUG`;
- `MediaRankUG`;
- `OpenSourceRankUG`;
- `ResearchRankUG`;
- `CommunityRankUG`.

Each index version must define:

- candidate universe;
- eligibility rules;
- required and optional metrics;
- normalization method;
- formula/weights;
- freshness or time-decay logic;
- missing-data behavior;
- anomaly/manipulation treatment;
- confidence rules;
- tie-breaking;
- validation method;
- known limitations.

### 7.3 TREND

A ranking based mainly on movement, growth, velocity, or change during a defined period.

Examples:

- fastest-growing channels;
- biggest rank movers;
- rising developers;
- breakout startups;
- fastest-growing repositories.

## 8. Ranking principles

### 8.1 Deterministic official rankings

Gemini or another LLM must not directly choose official winners or assign official ranks.

The invariant is:

> **AI interprets evidence; TopTenUG calculates rankings.**

LLMs can help identify candidates, classify evidence, resolve ambiguous identity clues, detect anomalies, and explain an already-computed result. Official ranking output is generated by versioned deterministic logic from stored metrics.

### 8.2 Normalization

Different metrics require different treatments. Supported approaches may include:

- logarithmic transformation for heavy-tailed counts;
- percentile ranks;
- robust z-scores;
- min/max normalization within a defined candidate universe;
- capped outliers;
- time decay;
- engagement ratios;
- growth rates;
- confidence-weighted contributions.

Normalization must be defined by the ranking specification rather than selected ad hoc at runtime.

### 8.3 Ranking Lab

A later public feature may allow users to adjust ranking weights interactively and see a simulated leaderboard.

User simulations must be clearly labeled as **unofficial** and must never replace the published quarterly index.

## 9. Data architecture

TopTenUG uses three conceptual data layers.

### 9.1 Raw observations

Immutable or append-oriented observations retain what a source reported at a particular time.

Representative fields:

```text
source
source_record_id
entity_id
metric
raw_value
unit
observed_at
retrieved_at
source_url
source_confidence
retrieval_method
```

A later observation does not overwrite historical values.

### 9.2 Derived metrics

Derived metrics are calculated from raw observations and may include:

- 90-day growth;
- engagement rate;
- repository adoption score;
- activity consistency;
- cross-platform reach;
- research recency;
- evidence confidence;
- category-specific normalized factors.

Derived metrics are versioned or reproducible from their inputs.

### 9.3 Ranking results

Representative ranking result fields:

```text
ranking_id
category_id
quarter
ranking_type
algorithm_name
algorithm_version
entity_id
score
rank
previous_rank
movement
confidence
published_at
```

Official ranking results are snapshots and are not silently rewritten by continuously arriving data.

## 10. Continuous ingestion and quarterly publication

TopTenUG separates **data freshness** from **official ranking stability**.

During a quarter, the platform continuously or periodically:

1. discovers candidates;
2. ingests source data;
3. stores observations;
4. resolves or flags entity matches;
5. extracts evidence;
6. computes provisional derived metrics;
7. detects source failures, anomalies, and coverage gaps;
8. generates internal/provisional ranking signals.

At quarter close:

```text
Data freeze
   ↓
Validation
   ↓
Deduplication / entity review
   ↓
Eligibility evaluation
   ↓
Metric derivation
   ↓
Algorithm execution
   ↓
Anomaly review
   ↓
Official snapshot
   ↓
Publish
```

The official quarter remains stable even while the next quarter's data is being collected.

The public UI may show a non-numeric **live trend direction** based on newer data, but it must distinguish that from the official published rank.

## 11. Data-source hierarchy

TopTenUG should favor evidence in this order when practical:

### Level A — authoritative structured source

Examples: official APIs, open government data, GitHub API, YouTube Data API, Crossref, OpenAlex, ORCID, official registries, or direct public datasets.

### Level B — first-party public evidence

Examples: official organization websites, personal websites, university profiles, official social profiles, project websites.

### Level C — reputable third-party evidence

Examples: established media, conferences, journals, industry databases, recognized ecosystem publications.

### Level D — broader public-web evidence

Search-discovered sources that do not fit higher confidence levels.

### Level E — AI inference

AI inference is never accepted alone as authoritative evidence. It must point back to evidence from Levels A-D before affecting official data.

## 12. Google and Gemini intelligence layer

Google is the preferred discovery and grounding ecosystem; Gemini is the primary GenAI/ML layer.

The Google/Gemini layer may support:

- broad candidate discovery using grounded web search;
- search-query generation;
- URL research and evidence synthesis;
- structured extraction into controlled schemas;
- taxonomy classification;
- entity-resolution suggestions;
- anomaly investigation;
- evidence summarization;
- semantic embeddings and retrieval;
- source/claim grounding checks;
- ranking explanations generated from already-computed factors;
- quarterly research summaries.

Source-specific APIs remain preferred for hard metrics when available.

Google semantic ranking/retrieval tools may rerank documents or evidence for relevance, but they do not directly determine TopTenUG's official entity ranking.

The AI boundary should be provider-abstracted so that product logic does not depend on Gemini calls scattered throughout the codebase. Gemini is the default implementation, not a hidden dependency embedded in ranking formulas.

## 13. Agent architecture

Potential specialized agents include:

- `DiscoveryAgent`;
- `GitHubAgent`;
- `YouTubeAgent`;
- `MediaAgent`;
- `StartupAgent`;
- `ResearchAgent`;
- `WebEvidenceAgent`;
- `EntityResolutionAgent`;
- `VerificationAgent`;
- `AnomalyAgent`;
- `QuarterlyResearchAgent`.

Agents communicate through explicit structured contracts. Agent output is evidence/proposals, not an official rank.

A2A may later coordinate independent specialist agents. MCP is used for tool/data access and for exposing TopTenUG capabilities to external AI clients.

## 14. MCP surface

A future TopTenUG MCP server may expose tools such as:

```text
search_entities
get_entity
get_rankings
get_top_10
get_top_50
compare_entities
explain_rank
get_rank_history
get_quarter
search_evidence
get_trending
get_methodology
```

MCP responses should preserve quarter, algorithm version, and evidence provenance where relevant.

## 15. Share-card engine

Share cards are a first-class product feature and growth mechanism.

Cards are generated from official ranking data and may represent:

- current ranking position;
- category leader;
- new Top 10 entrant;
- biggest mover;
- Top 10 streak;
- quarterly milestone;
- metric achievement;
- category summary.

Supported output formats should include:

- 1:1 square;
- 4:5 portrait;
- 9:16 story/status;
- landscape/OpenGraph.

Supported actions should include:

- download PNG/WebP;
- copy ranking link;
- native device share where supported;
- social-platform-friendly previews.

Cards may contain a QR code or short URL back to the canonical ranking/profile page.

A card must be generated from an official snapshot so that a user cannot change the displayed rank while retaining an official-looking TopTenUG artifact.

## 16. Main dashboard analytics

The main and category dashboards may expose interactive analytics such as:

- total indexed entities;
- active rankings;
- source coverage;
- observation counts;
- biggest movers;
- new entrants;
- ecosystem/category growth;
- social-platform distribution;
- startup-sector distribution;
- geographic distribution when sufficiently supported;
- represented universities;
- programming-language trends;
- technology trends;
- ranking history;
- score history;
- source-coverage/confidence views.

Charts should be actionable: clicking a visualization should navigate to the relevant ranking or filtered view when possible.

## 17. Search

TopTenUG should eventually support both structured filtering and semantic discovery.

Example semantic queries:

- "Ugandan developers doing agricultural AI";
- "startups working on agriculture and mobile payments";
- "women who entered an AI Top 10 in the last four quarters";
- "fast-growing technology YouTube channels".

Semantic retrieval identifies relevant entities/evidence; it does not bypass official ranking algorithms.

## 18. Corrections, disputes, and ranking integrity

Because TopTenUG may rank real people and organizations, the project needs an explicit correction process.

A correction should:

1. identify the entity, observation, identity match, eligibility claim, or source at issue;
2. provide public supporting evidence;
3. update or invalidate the underlying evidence/observation;
4. recompute affected derived metrics and rankings when appropriate;
5. preserve an audit trail.

Published rank numbers should not be manually edited as the primary correction mechanism.

Methodology criticism is treated separately from factual data correction.

## 19. Privacy, safety, and source ethics

TopTenUG is based on public ecosystem intelligence, not invasive personal profiling.

The project should not intentionally ingest:

- private or leaked data;
- passwords, secrets, or private contact records;
- sensitive personal information that is irrelevant to a ranking;
- data obtained by bypassing access controls;
- unsupported allegations or inferred sensitive traits.

Public-web ingestion must respect applicable access rules, rate limits, source terms, and legal/ethical constraints.

The system should minimize retained personal data to what is needed for public identity resolution, evidence provenance, and the ranking purpose.

## 20. Error handling and data-quality behavior

The system should fail conservatively.

Examples:

- unavailable source: retain last known observation with staleness metadata rather than inventing a value;
- API rate limit: schedule retry and mark coverage status;
- conflicting identity evidence: do not auto-merge below the configured confidence threshold;
- extreme metric jump: flag anomaly before allowing the signal to dominate a quarterly index;
- missing metric: use ranking-specific documented missing-data behavior rather than an implicit zero unless zero is semantically correct;
- extraction uncertainty: store confidence and source references;
- failed quarter pipeline: do not publish a partial snapshot as official.

## 21. Testing and validation

The implementation should eventually include:

### Unit tests

- normalization functions;
- score calculations;
- eligibility rules;
- tie-breaking;
- time decay;
- movement calculations;
- confidence weighting;
- share-card metadata generation.

### Contract tests

- source-adapter output schemas;
- AI structured-output schemas;
- agent contracts;
- API/MCP responses.

### Data-quality tests

- duplicate entities;
- impossible metric values;
- stale observations;
- missing provenance;
- quarter consistency;
- algorithm-version consistency;
- rank uniqueness where required.

### Ranking validation

Before publishing a new index version:

- run sensitivity analysis on weights;
- test outlier behavior;
- compare with previous versions;
- inspect major rank changes;
- evaluate missing-data bias;
- record expected limitations.

### End-to-end tests

At minimum, the full pipeline should be testable from source observation through a deterministic ranking snapshot and public leaderboard representation.

## 22. Open-contribution model

TopTenUG is open for community contributions.

Contributors may propose:

- new sources;
- new ranking categories;
- new index algorithms;
- source adapters;
- visualizations;
- Gemini workflows;
- entity-resolution improvements;
- statistical validation;
- MCP/A2A features;
- documentation and methodology analysis.

Changes affecting official ranking methodology require explicit documentation and versioning.

## 23. Scope boundaries for the first implementation cycle

The first implementation cycle should prove the platform architecture with a small number of high-quality ranking families rather than attempting hundreds of lists immediately.

The initial product should demonstrate:

- generic entities;
- at least one direct metric ranking;
- at least one composite index ranking;
- at least one trend ranking;
- historical observations;
- one quarterly snapshot flow;
- evidence/source provenance;
- Gemini-assisted discovery/extraction;
- a public dashboard;
- one category page;
- one profile page;
- Top 10 → Top 50 expansion;
- downloadable share cards;
- methodology display.

The architecture must allow additional categories without restructuring the core data model.

## 24. Explicit non-goals for the first cycle

The first cycle will not attempt to:

- rank every Ugandan or every industry;
- collect every social platform simultaneously;
- produce a universal score comparing fundamentally unrelated entities;
- fully automate disputed identity merges;
- treat AI-generated judgments as ranking evidence;
- build a commercial-grade data warehouse before the core ranking model works;
- expose unreviewed provisional rankings as official.

## 25. Architecture invariant summary

The project should preserve these invariants throughout implementation:

```text
Google discovers broadly.
Gemini interprets and structures evidence.
Source APIs provide authoritative metrics where possible.
TopTenUG stores history and provenance.
TopTenUG algorithms calculate official scores.
Official rankings are quarterly snapshots.
The public experience defaults to Top 10 and expands to 50 maximum.
Deep methodology and evidence remain inspectable.
Share cards turn official data into distribution.
MCP/A2A make the intelligence layer reusable by agents and external tools.
```

## 26. Implementation-stack boundary

This design intentionally specifies component responsibilities and interfaces before binding them to a final framework/cloud stack. The implementation plan following approval of this specification will select concrete technologies while preserving the invariants above. This prevents early framework choices from constraining the data model, ranking methodology, or contribution model.
