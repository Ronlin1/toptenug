# DevRankUG 1.0.0

DevRankUG is a TopTenUG-owned deterministic index for eligible Ugandan or Uganda-based technology builders. Google Search, Gemini, and other discovery systems can help TopTenUG find candidates and evidence, but **their relevance/order is never a ranking factor**.

## Factors

| Factor | Weight | Metric | Normalization |
|---|---:|---|---|
| Project adoption | 30% | `github.owned_repo_stars` | `log1p` |
| Contribution activity | 25% | `github.contributions_90d` | percentile |
| Project breadth | 15% | `github.active_owned_repos_180d` | capped min-max |
| Audience | 10% | `github.followers` | `log1p` |
| Collaboration | 20% | `github.prs_and_reviews_90d` | percentile |

Scores are calculated on a 0-100 scale. Missing factors use `renormalize_available`: only available factor weights contribute to the score. An official publication requires at least 60% configured factor coverage; the ranking engine records lower-coverage calculations for validation/debugging, but the quarterly publication gate must block them from an official result.

Ties are resolved deterministically by canonical entity UUID. The candidate universe is fixed for a ranking run, so normalizations are reproducible for frozen inputs.

## Limitations

This first version intentionally uses GitHub hard metrics only. It does not claim to measure every dimension of software-engineering quality, private work, employment performance, mentorship, or societal impact. Future methodology versions can add validated signals, but changes require a new version and documented validation.
