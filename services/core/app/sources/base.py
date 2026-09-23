from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from app.domain.schemas import ObservationInput


@dataclass(frozen=True)
class EntityRef:
    id: UUID
    external_id: str


class SourceError(RuntimeError):
    pass


class SourceNotFoundError(SourceError):
    pass


class RetryableSourceError(SourceError):
    def __init__(self, message: str, *, retry_after_seconds: int | None = None, reset_at: str | None = None):
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds
        self.reset_at = reset_at


class SourceAdapter(Protocol):
    async def collect(self, entity: EntityRef) -> list[ObservationInput]: ...
