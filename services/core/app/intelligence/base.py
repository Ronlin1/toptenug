from __future__ import annotations
from typing import Any,Protocol,TypeVar
from pydantic import BaseModel
from app.domain.schemas import CandidateProposal,DiscoveryQuery
T=TypeVar('T',bound=BaseModel)
class IntelligenceProvider(Protocol):
    def discover(self,query:DiscoveryQuery)->list[CandidateProposal]: ...
    def extract_evidence(self,url:str,schema:type[T])->list[T]: ...
def proposal_to_candidate_record(p:CandidateProposal)->dict[str,Any]:return {**p.model_dump(mode='json'),'official_rank':None,'official_score':None}
