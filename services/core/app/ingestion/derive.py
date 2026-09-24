from collections.abc import Iterable
from uuid import UUID
from app.ranking.engine import CandidateMetrics
from .pipeline import InMemoryIngestionRepository,StoredObservation
def _latest(rows:Iterable[StoredObservation],eid:UUID)->dict[str,StoredObservation]:
    out={}
    for row in rows:
        if row.entity_id==eid and (row.metric_key not in out or row.observed_at>out[row.metric_key].observed_at):out[row.metric_key]=row
    return out
def derive_candidate_metrics(repo:InMemoryIngestionRepository,eid:UUID,*,eligible:bool)->CandidateMetrics:
    latest=_latest(repo.observations,eid);metrics={k:float(r.raw_value) for k,r in latest.items() if isinstance(r.raw_value,(int,float)) and not isinstance(r.raw_value,bool)};return CandidateMetrics(eid,metrics,eligible)
