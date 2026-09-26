from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_reports_environment_and_commit_without_secret_values(monkeypatch) -> None:
    monkeypatch.setattr("app.main.database_reachable", lambda: True)
    monkeypatch.setattr("app.main.settings.environment", "staging", raising=False)
    monkeypatch.setattr("app.main.settings.commit_sha", "abc1234", raising=False)

    response = client.get("/ready")

    assert response.status_code == 200
    payload = response.json()
    assert payload == {
        "status": "ready",
        "environment": "staging",
        "commit_sha": "abc1234",
        "database_reachable": True,
        "version": "0.1.0",
    }
    rendered = str(payload)
    assert "DATABASE_URL" not in rendered
    assert "postgresql" not in rendered
    assert "GITHUB_TOKEN" not in rendered
    assert "GEMINI_API_KEY" not in rendered
