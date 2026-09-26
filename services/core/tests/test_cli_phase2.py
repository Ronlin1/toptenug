from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID, uuid4

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from typer.testing import CliRunner

from app.cli import app
from app.domain.enums import EntityType
from app.domain.models import Base, CandidateRecord
from app.domain.schemas import CandidateProposal

runner = CliRunner()


class FakeIntelligenceProvider:
    def __init__(self, **_: object) -> None:
        pass

    def discover(self, _query: object) -> list[CandidateProposal]:
        return [
            CandidateProposal(
                display_name="CLI Candidate",
                entity_type=EntityType.PERSON,
                candidate_profiles={"github": "cli-candidate"},
                uganda_relation_claims=["Ugandan developer"],
                source_urls=["https://example.com/cli-candidate"],
                confidence=0.95,
            )
        ]


def test_discover_persist_outputs_counts_not_candidate_order(monkeypatch) -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine)
    monkeypatch.setattr("app.cli.GeminiIntelligenceProvider", FakeIntelligenceProvider)
    monkeypatch.setattr("app.cli._session_local", lambda: factory)

    result = runner.invoke(app, ["discover", "--universe", "technology", "--persist"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload == {
        "created": 1,
        "proposals": 1,
        "review_required": 0,
        "updated": 0,
    }
    assert "CLI Candidate" not in result.output
    with Session(engine) as session:
        assert session.scalar(select(CandidateRecord)) is not None


def test_review_command_group_exposes_list_approve_and_reject() -> None:
    result = runner.invoke(app, ["review", "--help"])

    assert result.exit_code == 0
    assert "list" in result.output
    assert "approve" in result.output
    assert "reject" in result.output


def _batch_result(entity_ids: list[UUID]) -> SimpleNamespace:
    return SimpleNamespace(
        run_id=uuid4(),
        attempted=len(entity_ids),
        succeeded=len(entity_ids),
        failed=0,
        observations_added=len(entity_ids),
        failures=(),
    )


def test_github_batch_cli_defaults_to_reviewed_eligible_selection(monkeypatch) -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine)
    selected = [uuid4(), uuid4()]
    calls: dict[str, object] = {}

    def fake_select(_session: Session, *, limit: int) -> list[UUID]:
        calls["limit"] = limit
        return selected

    async def fake_batch(_session: Session, entity_ids: list[UUID], **_: object) -> SimpleNamespace:
        calls["entity_ids"] = entity_ids
        return _batch_result(entity_ids)

    monkeypatch.setattr("app.cli._session_local", lambda: factory)
    monkeypatch.setattr("app.cli.eligible_github_entity_ids", fake_select)
    monkeypatch.setattr("app.cli.ingest_github_batch", fake_batch)

    result = runner.invoke(app, ["ingest", "github-batch", "--limit", "2"])

    assert result.exit_code == 0, result.output
    assert calls == {"limit": 2, "entity_ids": selected}
    payload = json.loads(result.output)
    assert payload["attempted"] == 2
    assert payload["failed"] == 0


def test_github_batch_cli_reads_explicit_entity_file(monkeypatch, tmp_path: Path) -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine)
    entity_ids = [uuid4(), uuid4()]
    entity_file = tmp_path / "entities.txt"
    entity_file.write_text("\n".join(str(value) for value in entity_ids) + "\n", encoding="utf-8")
    calls: dict[str, object] = {}

    def forbidden_select(_session: Session, *, limit: int) -> list[UUID]:
        raise AssertionError(f"default selection should not run for explicit file; limit={limit}")

    async def fake_batch(_session: Session, selected: list[UUID], **_: object) -> SimpleNamespace:
        calls["entity_ids"] = selected
        return _batch_result(selected)

    monkeypatch.setattr("app.cli._session_local", lambda: factory)
    monkeypatch.setattr("app.cli.eligible_github_entity_ids", forbidden_select)
    monkeypatch.setattr("app.cli.ingest_github_batch", fake_batch)

    result = runner.invoke(
        app,
        ["ingest", "github-batch", "--entity-file", str(entity_file)],
    )

    assert result.exit_code == 0, result.output
    assert calls["entity_ids"] == entity_ids
