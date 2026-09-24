from dataclasses import dataclass
from typing import Protocol
from uuid import UUID
from app.domain.schemas import CandidateProposal
class ResolutionRepository(Protocol):
    def entity_ids_for_profile(self,profile_url:str)->set[UUID]: ...
    def entity_ids_for_name(self,display_name:str)->set[UUID]: ...
@dataclass(frozen=True)
class Resolution:
    entity_id:UUID|None
    review_required:bool
    reason:str
class EntityResolutionService:
    def __init__(self,repository:ResolutionRepository)->None:self.repository=repository
    def resolve(self,proposal:CandidateProposal)->Resolution:
        ids:set[UUID]=set()
        for url in proposal.candidate_profiles.values():ids|=self.repository.entity_ids_for_profile(url)
        if len(ids)==1:return Resolution(next(iter(ids)),False,'exact_profile')
        if len(ids)>1:return Resolution(None,True,'conflicting_profiles')
        if self.repository.entity_ids_for_name(proposal.display_name):return Resolution(None,True,'name_only_match')
        return Resolution(None,False,'new_entity')
