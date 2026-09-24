from pathlib import Path
from uuid import UUID,uuid4
from app.ranking.engine import CandidateMetrics,RankingEngine
from app.ranking.loader import load_algorithm_spec
def _spec(): return load_algorithm_spec(Path('algorithms/devrankug/v1.0.0.yaml'))
def _candidates():
    m={'github.owned_repo_stars':100,'github.contributions_90d':50,'github.active_owned_repos_180d':5,'github.followers':1000,'github.prs_and_reviews_90d':15}
    return [CandidateMetrics(UUID(int=2),m),CandidateMetrics(UUID(int=1),m)]
def test_same_inputs_produce_same_order(): assert RankingEngine().run(_spec(),_candidates())==RankingEngine().run(_spec(),_candidates())
def test_missing_metric_uses_declared_policy():
    r=RankingEngine().run(_spec(),[CandidateMetrics(uuid4(),{'github.followers':None})])[0]; assert r.factor_breakdown['audience'].missing_policy=='renormalize_available'; assert r.qualified is False
def test_stable_tie_breaking_by_canonical_uuid():
    r=RankingEngine().run(_spec(),_candidates()); assert [x.entity_id for x in r]==sorted(x.entity_id for x in r); assert [x.rank for x in r]==[1,2]
def test_engine_has_no_ai_dependency():
    s=Path('app/ranking/engine.py').read_text(); assert 'google.genai' not in s; assert 'Gemini' not in s
