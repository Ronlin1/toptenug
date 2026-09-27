from pathlib import Path


def _workflow_text() -> str:
    root = Path(__file__).resolve().parents[4]
    return (root / ".github" / "workflows" / "deploy.yml").read_text(encoding="utf-8")


def test_deploy_workflow_is_manual_only() -> None:
    text = _workflow_text()
    trigger_block = text.split("jobs:", 1)[0]

    assert "workflow_dispatch:" in trigger_block
    assert "push:" not in trigger_block
    assert "pull_request:" not in trigger_block


def test_deploy_workflow_requires_environment_and_commit_inputs() -> None:
    text = _workflow_text()

    assert "environment:" in text
    assert "commit_sha:" in text
    assert "staging" in text
    assert "production" in text


def test_deploy_workflow_runs_config_validation_before_external_deploy_commands() -> None:
    text = _workflow_text()
    validator = text.index("validate_deployment_config.py")
    first_external = min(
        index for index in (text.find("gcloud run"), text.find("vercel")) if index >= 0
    )

    assert validator < first_external
