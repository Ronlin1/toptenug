from __future__ import annotations
from datetime import datetime
from typing import Protocol
from app.domain.schemas import EntityRef, ObservationInput

class SourceError(RuntimeError):
    pass

class RetryableSourceError(SourceError):
    def __init__(self,message:str,*,retry_after_seconds:int|None=None,reset_at:datetime|None=None)->None:
        super().__init__(message)
        self.retry_after_seconds=retry_after_seconds
        self.reset_at=reset_at

class SourceAdapter(Protocol):
    async def collect(self,entity:EntityRef)->list[ObservationInput]: ...
