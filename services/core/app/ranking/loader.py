from __future__ import annotations
from pathlib import Path
import yaml
from pydantic import BaseModel,Field,model_validator
from app.domain.enums import RankingType
class FactorSpec(BaseModel): weight:float=Field(gt=0,le=1); metric:str; normalization:str
class AlgorithmSpec(BaseModel):
    name:str; version:str; ranking_type:RankingType; eligibility_policy:str; missing_data_policy:str='renormalize_available'; minimum_factor_coverage:float=Field(default=0,ge=0,le=1); tie_breaker:str='canonical_entity_id'; factors:dict[str,FactorSpec]=Field(default_factory=dict); metric:str|None=None; normalization:str='min_max'; baseline_metric:str|None=None
    @model_validator(mode='after')
    def validate_shape(self)->'AlgorithmSpec':
        if self.ranking_type==RankingType.INDEX and not self.factors: raise ValueError('INDEX algorithm requires factors')
        if self.ranking_type in {RankingType.METRIC,RankingType.TREND} and not self.metric: raise ValueError(f'{self.ranking_type} algorithm requires metric')
        if self.ranking_type==RankingType.TREND and not self.baseline_metric: raise ValueError('TREND algorithm requires baseline_metric')
        return self
def load_algorithm_spec(path:Path)->AlgorithmSpec: return AlgorithmSpec.model_validate(yaml.safe_load(path.read_text()))
