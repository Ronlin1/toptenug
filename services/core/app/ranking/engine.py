from __future__ import annotations
from dataclasses import dataclass,replace
from uuid import UUID
from app.domain.enums import RankingType
from .index import FactorScore,weighted_index
from .loader import AlgorithmSpec
from .normalizers import normalize
from .trend import percent_change
@dataclass(frozen=True)
class CandidateMetrics: entity_id:UUID; metrics:dict[str,float|int|None]; eligible:bool=True
@dataclass(frozen=True)
class ScoredCandidate: entity_id:UUID; score:float; rank:int; factor_breakdown:dict[str,FactorScore]; factor_coverage:float; qualified:bool
class RankingEngine:
    @staticmethod
    def _rank(rows:list[ScoredCandidate])->list[ScoredCandidate]:
        ordered=sorted(rows,key=lambda r:(-r.score,str(r.entity_id)))
        return [replace(r,rank=i) for i,r in enumerate(ordered,1)]
    def run(self,spec:AlgorithmSpec,candidates:list[CandidateMetrics])->list[ScoredCandidate]:
        if not candidates:return []
        scored=self._index(spec,candidates) if spec.ranking_type==RankingType.INDEX else self._metric(spec,candidates) if spec.ranking_type==RankingType.METRIC else self._trend(spec,candidates)
        return self._rank(scored)
    def run_metric(self,metric:str,candidates:list[CandidateMetrics])->list[ScoredCandidate]:
        rows=[]
        for c in candidates:
            raw=c.metrics.get(metric)
            if not c.eligible or raw is None:continue
            value=float(raw)
            rows.append(ScoredCandidate(c.entity_id,value,0,{'metric':FactorScore(value,None,1.0,value,'exclude_missing')},1.0,True))
        return self._rank(rows)
    def run_trend(self,metric:str,*,current:list[CandidateMetrics],baseline:list[CandidateMetrics])->list[ScoredCandidate]:
        baseline_by_id={c.entity_id:c for c in baseline}
        rows=[]
        for c in current:
            if not c.eligible:continue
            prior=baseline_by_id.get(c.entity_id)
            if prior is None:continue
            change=percent_change(c.metrics.get(metric),prior.metrics.get(metric))
            if change is None:continue
            rows.append(ScoredCandidate(c.entity_id,change,0,{'trend':FactorScore(change,None,1.0,change,'require_valid_baseline')},1.0,True))
        return self._rank(rows)
    def _index(self,spec:AlgorithmSpec,candidates:list[CandidateMetrics])->list[ScoredCandidate]:
        norm_by_metric={}
        for f in spec.factors.values():
            vals=[c.metrics.get(f.metric) for c in candidates]; norms=normalize(f.normalization,vals); norm_by_metric[f.metric]={c.entity_id:n for c,n in zip(candidates,norms,strict=True)}
        rows=[]
        for c in candidates:
            norm={m:by[c.entity_id] for m,by in norm_by_metric.items()}; score,cov,b=weighted_index(spec,c.metrics,norm); rows.append(ScoredCandidate(c.entity_id,round(score,8),0,b,round(cov,8),c.eligible and cov>=spec.minimum_factor_coverage))
        return rows
    def _metric(self,spec:AlgorithmSpec,candidates:list[CandidateMetrics])->list[ScoredCandidate]:
        assert spec.metric is not None
        vals=[c.metrics.get(spec.metric) for c in candidates]; norms=normalize(spec.normalization,vals); rows=[]
        for c,n in zip(candidates,norms,strict=True):
            raw=c.metrics.get(spec.metric); b={'metric':FactorScore(None if raw is None else float(raw),n,1,n or 0,spec.missing_data_policy)}; rows.append(ScoredCandidate(c.entity_id,round((n or 0)*100,8),0,b,1 if raw is not None else 0,c.eligible and raw is not None and n is not None))
        return rows
    def _trend(self,spec:AlgorithmSpec,candidates:list[CandidateMetrics])->list[ScoredCandidate]:
        assert spec.metric and spec.baseline_metric
        changes=[percent_change(c.metrics.get(spec.metric),c.metrics.get(spec.baseline_metric)) for c in candidates]; norms=normalize(spec.normalization,changes); rows=[]
        for c,ch,n in zip(candidates,changes,norms,strict=True):
            b={'trend':FactorScore(ch,n,1,n or 0,'require_valid_baseline')}; rows.append(ScoredCandidate(c.entity_id,round((n or 0)*100,8),0,b,1 if ch is not None else 0,c.eligible and ch is not None and n is not None))
        return rows
