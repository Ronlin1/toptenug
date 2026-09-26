from __future__ import annotations

import json

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
