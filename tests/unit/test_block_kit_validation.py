import re
from pathlib import Path

SKILL = Path("skills/block-kit/SKILL.md").read_text()
PROSE = " ".join(SKILL.split())


def test_all_requested_simplifications_remain_applied() -> None:
    frontmatter = SKILL.split("---", 2)[1]
    step_two = SKILL.split("## Step 2:", 1)[1].split("## Step 3:", 1)[0]
    step_three = SKILL.split("## Step 3:", 1)[1].split("## Step 4:", 1)[0]
    step_five_b = SKILL.split("### 5b. Handle the response", 1)[1].split(
        "## Step 6:", 1
    )[0]

    assert "argument-hint:" not in frontmatter
    assert "$0" not in SKILL
    assert re.search(r"\bdevelopers?\b", SKILL, re.IGNORECASE) is None
    assert "references/common-patterns.md" in step_two
    assert '"A feedback form with a text input and a category selector"' not in step_two
    assert "Surface constraints to check" not in step_three
    assert "Explain the error" not in step_five_b


def test_tooling_is_resolved_before_every_workflow_path() -> None:
    resolve_tooling = SKILL.index("## Resolve Tooling")
    fast_path = SKILL.index("## Fast Path")
    modification_mode = SKILL.index("## Modification Mode")
    validate = SKILL.index("## Step 5: Validate")
    assert resolve_tooling < fast_path < modification_mode < validate
    assert "`slack:slack-cli` skill, **Step 1: Detect the Slack CLI**" in SKILL
    assert SKILL.count("**Step 1: Detect the Slack CLI**") == 1
    assert "alias inquiry/verification branch" in PROSE
    assert "Do not propose installation unless the user independently asked" in PROSE
    assert "installed under a different name or alias. If the user supplies an alias," in SKILL
    assert "verify it with `<alias> _fingerprint 2>/dev/null` before setting `SLACK_CMD`." in SKILL
    assert "If no alias is supplied or verified, record the CLI as unavailable and use" in SKILL
    assert "Reuse the `SLACK_CMD` recorded in **Resolve Tooling**" in SKILL


def test_cli_validation_contract_is_explicit() -> None:
    assert "MUST attempt validation with the Slack CLI" in SKILL
    assert "$SLACK_CMD api blocks.validate --no-auth 'blocks=[...]'" in SKILL
    assert "$SLACK_CMD api blocks.validate --no-auth 'view={...}'" in SKILL
    assert "attempt it directly without running `api --help`" in PROSE
    assert 'validation response with `"ok": false`' in SKILL
    assert "retry with the CLI rather than switching transports" in SKILL
    assert "documented exception to that skill's generic help-first rule" in PROSE


def test_permission_retry_does_not_bypass_host_policy() -> None:
    assert "retry the identical command" in SKILL
    assert "Never activate a permission bypass" in SKILL
    assert "do not use another transport to evade that boundary" in SKILL
    assert (
        "If permission is denied or unavailable, preserve the error, report"
        ' that validation did not run, and stop' in PROSE
    )


def test_cli_execution_failure_can_fall_back_with_precise_disclosure() -> None:
    assert "the canonical CLI invocation cannot execute for a non-permission reason" in PROSE
    assert "record its version and diagnostic help output, then use curl" in PROSE
    assert "Retain the exact absence or execution-failure reason for Step 6" in PROSE
    assert "Validation transport: Slack CLI (<resolved command>)." in SKILL
    assert "Validation transport: curl (Slack CLI unavailable: <reason>)." in SKILL
    assert "Validation transport: curl (Slack CLI execution failure: <reason>; version/help recorded)." in SKILL
    assert "Validation status: not validated" in SKILL
    assert "Do not silently invent a different CLI invocation." in PROSE


def test_semantic_payload_and_network_failures_stay_on_cli() -> None:
    assert 'A parsed Slack semantic `"ok": false` response' in SKILL
    assert "payload error" in SKILL
    assert "network/service failure still counts as the CLI path executing" in PROSE
    assert "rather than switching transports" in PROSE


def test_absence_can_use_curl() -> None:
    fallback = SKILL.split("**Path B: curl (fallback).**", 1)[1].split(
        "### 5b. Handle the response", 1
    )[0]
    assert "resolved preflight state says the CLI is absent" in fallback


def test_preview_and_iteration_reuse_the_simplified_user_facing_contract() -> None:
    preview = SKILL.split("### Preview it", 1)[1].split("## Step 7:", 1)[0]
    assert "Reuse the `SLACK_CMD` recorded in **Resolve Tooling**" in preview
    assert "developer" not in preview.lower()
    assert "user's browser" in preview
    assert "Ask whether the user wants to add, modify, remove, or reorder blocks" in SKILL
