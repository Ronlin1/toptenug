from __future__ import annotations
from collections.abc import Mapping
from dataclasses import dataclass
from .loader import AlgorithmSpec
@dataclass(frozen=True)
class FactorScore:
    raw_value:float|None; normalized_value:float|None; weight:float; contribution:float; missing_policy:str
def weighted_index(spec:AlgorithmSpec,raw_metrics:Mapping[str,float|int|None],normalized_metrics:Mapping[str,float|None])->tuple[float,float,dict[str,FactorScore]]:
    aw=0.0; total=0.0; breakdown={}
    for name,factor in spec.factors.items():
        raw=raw_metrics.get(factor.metric); norm=normalized_metrics.get(factor.metric); contribution=0.0
        if raw is not None and norm is not None: aw+=factor.weight; contribution=factor.weight*norm; total+=contribution
        breakdown[name]=FactorScore(None if raw is None else float(raw),norm,factor.weight,contribution,spec.missing_data_policy)
    if aw<=0:return 0.0,0.0,breakdown
    score=total/aw if spec.missing_data_policy=='renormalize_available' else total
    return score*100,aw,breakdown
