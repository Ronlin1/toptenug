# DevRankUG 1.0.0 methodology

DevRankUG is a TopTenUG-owned deterministic `INDEX`. Google Search, Gemini, search-result position, LLM preferences, and editorial ordering are not ranking factors.

| Factor | Weight | Metric | Normalization |
|---|---:|---|---|
| Project adoption | 30% | `github.owned_repo_stars` | `log1p` |
| Contribution activity | 25% | `github.contributions_90d` | percentile |
| Project breadth | 15% | `github.active_owned_repos_180d` | capped min-max |
| Audience | 10% | `github.followers` | `log1p` |
| Collaboration | 20% | `github.prs_and_reviews_90d` | percentile |

Candidates need 60% factor coverage. Missing factors use `renormalize_available`. Equal scores use canonical entity UUID. GitHub activity is not a universal measure of developer quality.
