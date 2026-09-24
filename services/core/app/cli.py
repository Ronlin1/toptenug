from __future__ import annotations
import asyncio,json
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict,dataclass
from datetime import UTC,datetime
from pathlib import Path
from typing import Any
from uuid import UUID,uuid4
import typer
from app.config import get_settings
from app.domain.schemas import DiscoveryQuery
from app.intelligence.gemini import GeminiIntelligenceProvider
from app.operations import derive_quarter,ingest_github_entity,publish_quarter,validate_quarter
app=typer.Typer(name='toptenug',help='TopTenUG ingestion and quarterly ranking operations.',no_args_is_help=True); ingest_app=typer.Typer(help='Collect hard metrics from authoritative source APIs.'); app.add_typer(ingest_app,name='ingest')
@dataclass
class JobRecord: id:str; job_type:str; status:str; started_at:str; finished_at:str|None; counts:dict[str,int]; failure_details:dict[str,str]|None; parameters:dict[str,str]
class JobRecorder:
    def __init__(self,path:Path|None=None)->None:self.path=path or Path('.toptenug/jobs.jsonl')
    def append(self,r:JobRecord)->None:self.path.parent.mkdir(parents=True,exist_ok=True); self.path.open('a',encoding='utf-8').write(json.dumps(asdict(r),sort_keys=True)+'\n')
    @contextmanager
    def track(self,job_type:str,**params:str)->Iterator[dict[str,int]]:
        start=datetime.now(UTC); jid=str(uuid4()); counts={}
        try:yield counts
        except Exception as exc:self.append(JobRecord(jid,job_type,'FAILED',start.isoformat(),datetime.now(UTC).isoformat(),counts,{'type':type(exc).__name__,'message':str(exc)},params)); raise
        else:self.append(JobRecord(jid,job_type,'SUCCEEDED',start.isoformat(),datetime.now(UTC).isoformat(),counts,None,params))
def _session_local()->Any:
    from app.db import SessionLocal
    return SessionLocal
def _dump(v:Any)->None:typer.echo(json.dumps(v,indent=2,default=str,sort_keys=True))
def _validate_quarter(v:str)->None:
    if not (len(v)==7 and v[4:6]=='-Q' and v[:4].isdigit() and v[6] in '1234'):raise typer.BadParameter('quarter must use YYYY-QN where N is 1..4')
@app.command()
def discover(universe:str=typer.Option(...,'--universe'))->None:
    settings=get_settings()
    with JobRecorder().track('discover',universe=universe) as counts:
        p=GeminiIntelligenceProvider(api_key=settings.gemini_api_key,model=settings.gemini_model).discover(DiscoveryQuery(text=f'Ugandan {universe} builders and public evidence')); counts['proposals']=len(p); _dump([x.model_dump(mode='json') for x in p])
@ingest_app.command('github')
def ingest_github(entity:UUID=typer.Option(...,'--entity'))->None:
    with JobRecorder().track('ingest-github',entity=str(entity)) as counts:
        with _session_local()() as session:inserted=asyncio.run(ingest_github_entity(session,entity))
        counts['observations']=inserted; _dump({'entity':str(entity),'observations_added':inserted})
@app.command()
def derive(quarter:str=typer.Option(...,'--quarter'))->None:
    _validate_quarter(quarter)
    with JobRecorder().track('derive',quarter=quarter) as counts:
        with _session_local()() as session:n=derive_quarter(session,quarter)
        counts['derived_metrics']=n; _dump({'quarter':quarter,'derived_metrics':n})
@app.command()
def validate(category:str=typer.Option(...,'--category'),quarter:str=typer.Option(...,'--quarter'))->None:
    _validate_quarter(quarter)
    with JobRecorder().track('validate',category=category,quarter=quarter) as counts:
        with _session_local()() as session:r=validate_quarter(session,category,quarter)
        counts['errors']=len(r.errors); counts['blocking_anomalies']=len(r.blocking_anomalies); _dump({'ok':r.ok,'errors':r.errors,'blocking_anomalies':r.blocking_anomalies})
        if not r.ok:raise typer.Exit(2)
@app.command()
def publish(category:str=typer.Option(...,'--category'),quarter:str=typer.Option(...,'--quarter'))->None:
    _validate_quarter(quarter)
    with JobRecorder().track('publish',category=category,quarter=quarter) as counts:
        with _session_local()() as session:r=publish_quarter(session,category,quarter)
        counts['published_runs']=1; _dump({'run_id':str(r.id),'status':r.status,'quarter':r.quarter})
def main()->None:app()
if __name__=='__main__':main()
