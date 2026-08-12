from pathlib import Path

SKILL = Path("skills/block-kit/SKILL.md").read_text()


def test_tooling_is_resolved_before_every_workflow_path() -> None:
    resolve_tooling = SKILL.index("## Resolve Tooling")
    fast_path = SKILL.index("## Fast Path")
    modification_mode = SKILL.index("## Modification Mode")
    validate = SKILL.index("## Step 5: Validate")
    assert resolve_tooling < fast_path < modification_mode < validate
    assert "`slack:slack-cli` skill, **Step 1: Detect the Slack CLI**" in SKILL
    assert SKILL.count("**Step 1: Detect the Slack CLI**") == 1
    assert "do not propose installation or ask about an alias" in SKILL
    assert "Reuse the `SLACK_CMD` recorded in **Resolve Tooling**" in SKILL


def test_cli_validation_contract_is_explicit() -> None:
    assert "MUST attempt validation with the Slack CLI" in SKILL
    assert "$SLACK_CMD api blocks.validate --no-auth 'blocks=[...]'" in SKILL
    assert "$SLACK_CMD api blocks.validate --no-auth 'view={...}'" in SKILL
    assert "attempt it directly without running `api --help`" in SKILL
    assert 'validation response with `"ok": false`' in SKILL
    assert "retry with the CLI rather than switching transports" in SKILL


def test_permission_retry_does_not_bypass_host_policy() -> None:
    assert "retry the identical command" in SKILL
    assert "Never activate a permission bypass" in SKILL
    assert "do not use another transport to evade that boundary" in SKILL


def test_fallback_and_transport_are_disclosed() -> None:
    assert "Retain the exact fallback reason for Step 6" in SKILL
    assert "Validation transport: Slack CLI (<resolved command>)." in SKILL
    assert "Validation transport: curl (Slack CLI unavailable: <reason>)." in SKILL
    assert "Validation status: not validated" in SKILL
    assert "Do not use\ncurl to hide payload errors" in SKILL
