# TopTenUG 🇺🇬

**Uganda, ranked by data.**

TopTenUG is an open, evidence-driven discovery and ranking platform for Uganda's digital ecosystem. It combines public APIs, public datasets, web research, ethical public-web extraction, Gemini-powered discovery and grounding, data engineering, ranking algorithms, MCP, A2A, and interactive visual analytics to publish transparent Top 10 rankings across technology, media, startups, social platforms, digital marketing, research, communities, products, and more.

The project is intentionally both **fun and serious**:

- a beautiful, viral public experience that people enjoy exploring and sharing;
- a technically ambitious hobby/portfolio project demonstrating modern data, AI, agentic, search, ranking, and analytics systems;
- a credible long-term Ugandan digital intelligence index whose rankings can be inspected, explained, reproduced, and cited.

## Core idea

TopTenUG continuously discovers and ingests public evidence, but publishes **official quarterly ranking snapshots**. Rankings show 10 entries by default and may expand to 20, 30, or **50 maximum**.

```text
Public APIs / public datasets / web / research / social metrics / GitHub / media
                                  ↓
                         Continuous ingestion
                                  ↓
                    Google + Gemini intelligence
                                  ↓
                 Entity resolution + evidence store
                                  ↓
                     Metrics + ranking algorithms
                                  ↓
                       Quarterly data freeze
                                  ↓
                      Official Top 10 / Top 50
                                  ↓
        Dashboards + profiles + share cards + API + MCP + A2A
```

## Product principles

1. **Rank evidence, not reputation.** Every meaningful ranking should be traceable to public evidence and methodology.
2. **AI interprets; TopTenUG calculates.** Gemini may discover, extract, classify, reconcile, verify, and explain evidence. Deterministic TopTenUG algorithms produce official scores and ranks.
3. **Official rankings are quarterly.** Data can refresh continuously, while published ranking snapshots remain stable for the quarter.
4. **Top 10 stays the default.** Leaderboards may expand to 50, but never become endless directories.
5. **Metric, Index, and Trend rankings stay distinct.** A direct metric such as subscribers is not presented as the same thing as a multi-signal TopTenUG index.
6. **Raw observations are preserved.** Historical evidence and snapshots enable rank history, growth analysis, and reproducibility.
7. **Methodologies are versioned.** Algorithm changes are explicit, inspectable, and associated with the quarter in which they were used.
8. **Public UX is simple; intelligence depth is optional.** Casual visitors can enjoy the rankings while researchers can inspect scores, evidence, methodology, and historical data.
9. **Shareability is native.** Ranking cards should be downloadable and shareable across social platforms.
10. **Open for contributions.** New data sources, ranking ideas, categories, visualizations, algorithms, documentation, and engineering improvements are welcome.

## Initial universes

TopTenUG will organize many leaderboards under a small set of logical, interactive category cards:

- **Technology & Builders** — developers, GitHub users, open source, AI/ML, data, cloud, DevOps, cybersecurity, Web3, mobile, backend, frontend, infrastructure, and emerging technology.
- **Startups & Innovation** — startups, founders, sectors, emerging ventures, funded and bootstrapped companies, SaaS, AI, fintech, agritech, healthtech, edtech, climate-tech, developer tools, and more.
- **Social & Creators** — LinkedIn, X, YouTube, TikTok, Instagram, creators, influencers, engagement, audience growth, and cross-platform presence.
- **Media** — television, radio, newspapers, digital publishers, news platforms, podcasts, media brands, streaming, and digital reach.
- **Digital Marketing** — marketers, agencies, SEO, social strategy, growth, content, performance marketing, brand strategy, digital campaigns, and digital-first brands.
- **Products & Tools** — Ugandan-built apps, SaaS, APIs, AI tools, developer tools, libraries, bots, MCP servers, agents, and platforms.
- **Research & Knowledge** — researchers, publications, citations, institutions, labs, computing research, AI research, research software, and recent impact.
- **Communities & Events** — developer communities, university groups, innovation hubs, hackathons, conferences, meetups, and ecosystem activity.
- **Education & Talent** — universities, coding schools, bootcamps, student builders, student founders, university open-source activity, and research output.
- **Companies & Digital Economy** — technology companies, telecoms, ISPs, software companies, digital services, fintech, e-commerce, and related digital businesses.
- **Quarterly Pulse** — biggest movers, new entrants, breakout creators, rising developers, emerging startups, trending repositories, products, technologies, and ecosystem stories.

The taxonomy is intentionally extensible; TopTenUG is a ranking platform rather than a hard-coded collection of pages.

## Ranking types

Every leaderboard should clearly identify its type:

- **METRIC** — directly observable public measurement, e.g. YouTube subscribers or GitHub stars.
- **INDEX** — a versioned TopTenUG algorithm combining multiple normalized signals.
- **TREND** — primarily based on growth, movement, velocity, or change over time.

Examples of first-party index families may include `DevRankUG`, `CreatorRankUG`, `StartupRankUG`, `MediaRankUG`, `OpenSourceRankUG`, `ResearchRankUG`, `CommunityRankUG`, and `GrowthRankUG`.

## Quarterly model

TopTenUG collects data during the quarter but treats the quarter-end snapshot as the official release:

```text
Discover → Ingest → Verify → Normalize → Score → Rank → Freeze → Snapshot → Publish
```

Historical snapshots should make it possible to answer questions such as:

- Who gained the most positions this quarter?
- Who remained in the Top 10 for the longest?
- Which Ugandan startup had the fastest digital growth?
- Which university has the largest representation in a selected technology category?
- Which technologies or platforms are gaining momentum?

## Google + Gemini

Google is the preferred discovery and grounding ecosystem. Gemini is the primary GenAI/ML layer for candidate discovery, structured extraction, classification, entity resolution assistance, grounded research, anomaly investigation, semantic retrieval, and explanation generation.

Source-specific APIs remain preferred for hard metrics when available. Google Search/grounding helps discover the web; TopTenUG structures the evidence; TopTenUG algorithms produce the official ranking.

## Share cards

Official ranking results should generate downloadable and shareable cards for:

- ranking position;
- new Top 10 entries;
- biggest movers;
- #1/category leaders;
- Top 10 streaks;
- quarterly milestones;
- metric achievements;
- category summaries.

Cards should support common social formats such as 1:1, 4:5, 9:16, and landscape/OpenGraph, plus PNG/WebP download, copy-link, and native share capabilities where supported.

## Open contribution areas

Contributors can help with:

- data connectors and public data sources;
- candidate discovery;
- entity resolution;
- ranking and normalization algorithms;
- statistical validation;
- Gemini/AI workflows;
- MCP and A2A integrations;
- backend APIs;
- database and data engineering;
- frontend and data visualization;
- accessibility and UX;
- ranking methodology documentation;
- Uganda ecosystem taxonomy;
- testing, observability, and security.

Read [CONTRIBUTING.md](CONTRIBUTING.md) before proposing a change.

## Project status

**Design / architecture phase.** No production implementation has been selected yet. The current design is documented in [`docs/superpowers/specs/2026-09-23-toptenug-design.md`](docs/superpowers/specs/2026-09-23-toptenug-design.md).

---

Built as an open exploration of Uganda's digital ecosystem. 🇺🇬
