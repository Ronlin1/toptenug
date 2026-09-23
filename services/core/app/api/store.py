from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.enums import RankingRunStatus, RankingType


@dataclass(frozen=True)
class PublicRankingResult:
    entity_id: UUID
    slug: str
    name: str
    rank: int
    score: float
    confidence: float
    previous_rank: int | None = None
    factor_breakdown: dict[str, object] | None = None
    evidence_urls: tuple[str, ...] = ()
    id: UUID | None = None


@dataclass(frozen=True)
class PublicRankingRun:
    id: UUID
    slug: str
    quarter: str
    ranking_type: RankingType
    algorithm_name: str
    algorithm_version: str
    status: RankingRunStatus
    published_at: datetime | None
    methodology_url: str
    results: tuple[PublicRankingResult, ...]


class PublicReadStore:
    def __init__(self) -> None:
        self.runs: list[PublicRankingRun] = []

    def clear(self) -> None:
        self.runs.clear()

    def add_run(self, run: PublicRankingRun) -> None:
        self.runs.append(run)

    def published_runs(self, slug: str | None = None) -> list[PublicRankingRun]:
        runs = [run for run in self.runs if run.status == RankingRunStatus.PUBLISHED]
        if slug is not None:
            runs = [run for run in runs if run.slug == slug]
        return sorted(runs, key=lambda run: run.quarter, reverse=True)

    def get_published(self, slug: str, quarter: str | None = None) -> PublicRankingRun | None:
        runs = self.published_runs(slug)
        if quarter is not None:
            return next((run for run in runs if run.quarter == quarter), None)
        return runs[0] if runs else None

    def find_published_result(self, result_id: UUID):
        for run in self.published_runs():
            for result in run.results:
                if result.id == result_id:
                    return run, result
        return None


public_store = PublicReadStore()
