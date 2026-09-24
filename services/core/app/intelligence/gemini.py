from __future__ import annotations
import importlib,json
from typing import Any,TypeVar
from pydantic import BaseModel
from app.domain.enums import ReviewStatus
from app.domain.schemas import CandidateProposal,DiscoveryQuery
T=TypeVar('T',bound=BaseModel)
class GroundingRequiredError(ValueError):pass
class GeminiIntelligenceProvider:
    def __init__(self,*,api_key:str|None,client:Any|None=None,model:str='gemini-2.5-flash')->None:
        self._model=model; self._types=None
        if client is not None:self._client=client;return
        if not api_key:raise ValueError('GEMINI_API_KEY is required when no client is injected')
        genai=importlib.import_module('google.genai');self._types=importlib.import_module('google.genai.types');self._client=genai.Client(api_key=api_key)
    def _validate(self,payload:list[dict[str,Any]]|list[CandidateProposal])->list[CandidateProposal]:
        out=[]
        for item in payload:
            p=item if isinstance(item,CandidateProposal) else CandidateProposal.model_validate(item)
            if not p.source_urls:raise GroundingRequiredError(f"Candidate '{p.display_name}' has no grounded source URL")
            if p.confidence<.85 or any(t in claim.lower() for claim in p.uganda_relation_claims for t in ('possibly','maybe','unclear','unverified')):p=p.model_copy(update={'review_status':ReviewStatus.REVIEW_REQUIRED})
            out.append(p)
        return out
    def discover(self,query:DiscoveryQuery)->list[CandidateProposal]:
        if hasattr(self._client,'discover'):return self._validate(self._client.discover(query.text))
        r=self._client.models.generate_content(model=self._model,contents='Discover grounded candidates. Do not rank, score, or declare winners. Query: '+query.text,config=self._types.GenerateContentConfig(tools=[self._types.Tool(google_search=self._types.GoogleSearch())],response_mime_type='application/json',response_schema=list[CandidateProposal]));return self._validate(json.loads(r.text or '[]'))
    def extract_evidence(self,url:str,schema:type[T])->list[T]:
        if hasattr(self._client,'extract'):return [x if isinstance(x,schema) else schema.model_validate(x) for x in self._client.extract(url,schema.__name__)]
        r=self._client.models.generate_content(model=self._model,contents=f'Extract only claims supported by this URL; do not infer rankings: {url}',config=self._types.GenerateContentConfig(tools=[self._types.Tool(url_context=self._types.UrlContext())],response_mime_type='application/json',response_schema=list[schema]));return [schema.model_validate(x) for x in json.loads(r.text or '[]')]
