from pathlib import Path
from uuid import UUID

from app.ranking.engine import CandidateMetrics, RankingEngine
from app.ranking.loader import load_algorithm_spec


def _candidates():
    return [
        CandidateMetrics(entity_id=UUID(int=2), metrics={
            "github.owned_repo_stars": 100,
            "github.contributions_90d": 50,
            "github.active_owned_repos_180d": 6,
            "github.followers": 120,
            "github.prs_and_reviews_90d": 22,
        }),
        CandidateMetrics(entity_id=UUID(int=1), metrics={
            "github.owned_repo_stars": 20,
            "github.contributions_90d": 80,
            "github.active_owned_repos_180d": 4,
            "github.followers": 40,
            "github.prs_and_reviews_90d": 30,
        }),
    ]


def test_same_inputs_produce_same_order():
    engine = RankingEngine()
    spec = load_algorithm_spec(Path("algorithms/devrankug/v1.0.0.yaml"))
    assert engine.run(spec, _candidates()) == engine.run(spec, _candidates())


def test_missing_metric_uses_declared_policy():
    engine = RankingEngine()
    spec = load_algorithm_spec(Path("algorithms/devrankug/v1.0.0.yaml"))
    candidate = CandidateMetrics(entity_id=UUID(int=3), metrics={"github.followers": None})
    result = engine.run(spec, [candidate])[0]
    assert result.factor_breakdown["audience"].missing_policy == "renormalize_available"


def test_ties_break_by_canonical_entity_id():
    engine = RankingEngine()
    spec = load_algorithm_spec(Path("algorithms/devrankug/v1.0.0.yaml"))
    same = {key: 1 for key in [
        "github.owned_repo_stars",
        "github.contributions_90d",
        "github.active_owned_repos_180d",
        "github.followers",
        "github.prs_and_reviews_90d",
    ]}
    results = engine.run(spec, [
        CandidateMetrics(entity_id=UUID(int=2), metrics=same),
        CandidateMetrics(entity_id=UUID(int=1), metrics=same),
    ])
    assert [r.entity_id for r in results] == [UUID(int=1), UUID(int=2)]


def test_engine_has_no_ai_dependency():
    source = Path("app/ranking/engine.py").read_text()
    assert "google.genai" not in source
    assert "Gemini" not in source


def test_metric_ranking_sorts_observable_metric_and_excludes_missing():
    engine = RankingEngine()
    candidates = [
        CandidateMetrics(entity_id=UUID(int=2), metrics={"github.followers": 10}),
        CandidateMetrics(entity_id=UUID(int=1), metrics={"github.followers": 25}),
        CandidateMetrics(entity_id=UUID(int=3), metrics={"github.followers": None}),
    ]
    results = engine.run_metric("github.followers", candidates)
    assert [(row.entity_id, row.score, row.rank) for row in results] == [
        (UUID(int=1), 25.0, 1),
        (UUID(int=2), 10.0, 2),
    ]


def test_trend_ranking_requires_baseline_and_ranks_growth():
    engine = RankingEngine()
    current = [
        CandidateMetrics(entity_id=UUID(int=1), metrics={"github.followers": 150}),
        CandidateMetrics(entity_id=UUID(int=2), metrics={"github.followers": 220}),
        CandidateMetrics(entity_id=UUID(int=3), metrics={"github.followers": 10}),
    ]
    baseline = [
        CandidateMetrics(entity_id=UUID(int=1), metrics={"github.followers": 100}),
        CandidateMetrics(entity_id=UUID(int=2), metrics={"github.followers": 200}),
    ]
    results = engine.run_trend("github.followers", current=current, baseline=baseline)
    assert [row.entity_id for row in results] == [UUID(int=1), UUID(int=2)]
    assert results[0].score == 0.5
    assert results[1].score == 0.1
