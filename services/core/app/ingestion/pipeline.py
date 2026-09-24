from dataclasses import dataclass,field
from datetime import UTC,datetime
from re import sub
from uuid import NAMESPACE_URL,UUID,uuid4,uuid5
from app.domain.enums import ReviewStatus
from app.domain.schemas import CandidateProposal,ObservationInput
from .entity_resolution import EntityResolutionService
@dataclass
class StoredEntity:
    id:UUID;name:str;slug:str;proposal:CandidateProposal;review_status:ReviewStatus=ReviewStatus.PENDING;aliases:set[str]=field(default_factory=set);profiles:set[str]=field(default_factory=set)
@dataclass(frozen=True)
class StoredEvidence:id:UUID;entity_id:UUID;source_url:str;retrieved_at:datetime;confidence:float
@dataclass(frozen=True)
class StoredObservation:entity_id:UUID;metric_key:str;raw_value:float|int|str;observed_at:datetime;source_url:str;evidence_id:UUID;source_record_id:str
@dataclass(frozen=True)
class IngestionOutcome:entity_id:UUID;created:bool;review_required:bool;observations_added:int
class InMemoryIngestionRepository:
    def __init__(self)->None:
        self.entities:dict[UUID,StoredEntity]={};self.evidence:list[StoredEvidence]=[];self.observations:list[StoredObservation]=[];self.source_failures=[];self._profiles={};self._names={};self._observation_keys=set()
    @staticmethod
    def _normalized_name(v:str)->str:return ' '.join(v.casefold().split())
    @staticmethod
    def _slug(v:str)->str:return sub(r'[^a-z0-9]+','-',v.casefold()).strip('-') or 'entity'
    def entity_ids_for_profile(self,url:str)->set[UUID]:return set(self._profiles.get(url.casefold().rstrip('/'),set()))
    def entity_ids_for_name(self,name:str)->set[UUID]:return set(self._names.get(self._normalized_name(name),set()))
    def create_entity(self,p:CandidateProposal)->StoredEntity:
        eid=uuid4();base=self._slug(p.display_name);slug=base;n=2;existing={e.slug for e in self.entities.values()}
        while slug in existing:slug=f'{base}-{n}';n+=1
        e=StoredEntity(eid,p.display_name,slug,p,aliases={p.display_name},profiles=set(p.candidate_profiles.values()));self.entities[eid]=e;self._names.setdefault(self._normalized_name(p.display_name),set()).add(eid)
        for url in e.profiles:self._profiles.setdefault(url.casefold().rstrip('/'),set()).add(eid)
        self.save_proposal_evidence(eid,p);return e
    def enrich_entity(self,eid:UUID,p:CandidateProposal)->None:
        e=self.entities[eid];e.aliases.add(p.display_name);self._names.setdefault(self._normalized_name(p.display_name),set()).add(eid)
        for url in p.candidate_profiles.values():e.profiles.add(url);self._profiles.setdefault(url.casefold().rstrip('/'),set()).add(eid)
        self.save_proposal_evidence(eid,p)
    def save_proposal_evidence(self,eid:UUID,p:CandidateProposal)->None:
        known={(e.entity_id,e.source_url) for e in self.evidence};now=datetime.now(UTC)
        for url in p.source_urls:
            if (eid,url) not in known:self.evidence.append(StoredEvidence(uuid5(NAMESPACE_URL,f'candidate:{eid}:{url}'),eid,url,now,p.confidence));known.add((eid,url))
    def save_observation(self,eid:UUID,row:ObservationInput)->bool:
        if not any(e.id==row.evidence_id for e in self.evidence):self.evidence.append(StoredEvidence(row.evidence_id,eid,row.source_url,datetime.now(UTC),1.0))
        record=row.source_record_id or str(row.evidence_id);key=(record,row.metric_key,row.observed_at)
        if key in self._observation_keys:return False
        self._observation_keys.add(key);self.observations.append(StoredObservation(eid,row.metric_key,row.raw_value,row.observed_at,row.source_url,row.evidence_id,record));return True
    def record_source_failure(self,key:str,message:str)->None:self.source_failures.append((key,message,datetime.now(UTC)))
class IngestionPipeline:
    def __init__(self,repository:InMemoryIngestionRepository)->None:self.repository=repository;self.resolver=EntityResolutionService(repository)
    def ingest(self,p:CandidateProposal,observations:list[ObservationInput])->IngestionOutcome:
        r=self.resolver.resolve(p);created=r.entity_id is None
        if r.entity_id is None:
            e=self.repository.create_entity(p)
            if r.review_required:e.review_status=ReviewStatus.REVIEW_REQUIRED
        else:e=self.repository.entities[r.entity_id];self.repository.enrich_entity(e.id,p)
        added=sum(1 for row in observations if self.repository.save_observation(e.id,row));return IngestionOutcome(e.id,created,r.review_required,added)
    def record_source_failure(self,key:str,message:str)->None:self.repository.record_source_failure(key,message)
