import json
from pathlib import Path

import pytest

from scripts.opencode_smoke import (
    CommandResult,
    SmokeFailure,
    assert_discovery,
    assert_exact_version,
    assert_read_only_tools,
    render_evidence,
)


def result(stdout: str, exit_code: int = 0) -> CommandResult:
    return CommandResult(exit_code=exit_code, stdout=stdout, stderr="")


def test_exact_version_accepts_opencode_1_18_18() -> None:
    # Arrange
    version = result("1.18.18\n")

    # Act
    assert_exact_version(version)

    # Assert
    assert version.exit_code == 0


@pytest.mark.parametrize("stdout", ["1.18.19\n", "", "OpenCode 1.18.18\n"])
def test_exact_version_rejects_every_other_output(stdout: str) -> None:
    # Arrange
    version = result(stdout)

    # Act / Assert
    with pytest.raises(SmokeFailure, match="exactly 1.18.18"):
        assert_exact_version(version)


def test_discovery_accepts_exact_repository_inventory() -> None:
    # Arrange
    skills = result(json.dumps([{"name": "block-kit"}, {"name": "slack-search"}]))
    config = result(json.dumps({"command": {"slack-find-discussions": {}, "slack-standup": {}}}))

    # Act
    assert_discovery(skills, config, {"block-kit", "slack-search"}, {"slack-find-discussions", "slack-standup"})

    # Assert
    assert skills.exit_code == config.exit_code == 0


def test_discovery_ignores_terminal_escape_sequences() -> None:
    # Arrange
    skills = result('\x1b[0m[{"name": "block-kit"}]\n')
    config = result('\x1b[0m{"command": {"slack-standup": {}}}\n')

    # Act
    assert_discovery(skills, config, {"block-kit"}, {"slack-standup"})

    # Assert
    assert skills.exit_code == config.exit_code == 0


def test_discovery_tolerates_truncated_skill_array() -> None:
    # Arrange: project skills are complete and leading; the truncated tail is a
    # large global skill (e.g. graphify) that is not part of the expected set.
    skills = result(
        '[{"name": "block-kit"}, {"name": "slack-search"}, '
        '{"name": "graphify", "content": "unterminated'
    )
    config = result(json.dumps({"command": {"slack-standup": {}}}))

    # Act
    assert_discovery(skills, config, {"block-kit", "slack-search"}, {"slack-standup"})

    # Assert
    assert skills.exit_code == config.exit_code == 0


def test_discovery_rejects_missing_or_extra_repository_artifacts() -> None:
    # Arrange
    skills = result(json.dumps([{"name": "block-kit"}]))
    config = result(json.dumps({"command": {"slack-find-discussions": {}, "slack-unexpected": {}}}))

    # Act / Assert
    with pytest.raises(SmokeFailure, match="skills missing"):
        assert_discovery(skills, config, {"block-kit", "slack-search"}, {"slack-find-discussions"})


def test_read_only_tools_accept_completed_search_or_read_calls() -> None:
    # Arrange
    observations = {"slack_search_public": "completed", "slack_read_thread": "completed"}

    # Act
    selected = assert_read_only_tools(observations)

    # Assert
    assert selected == ("slack_read_thread", "slack_search_public")


@pytest.mark.parametrize(
    ("observations", "message"),
    [
        ({"slack_send_message": "completed"}, "write-capable"),
        ({"slack_search_public": "error"}, "completed read-only"),
    ],
)
def test_read_only_tools_reject_writes_and_unsuccessful_reads(
    observations: dict[str, str],
    message: str,
) -> None:
    # Arrange
    selected = observations

    # Act / Assert
    with pytest.raises(SmokeFailure, match=message):
        assert_read_only_tools(selected)


def test_evidence_contains_only_statuses_and_tool_identities(tmp_path: Path) -> None:
    # Arrange
    secret = "123456789012.987654321098"
    workspace_content = "private launch message"

    # Act
    evidence = render_evidence(
        discovery_status="PASS",
        full_status="PASS",
        identities=("skill:block-kit", "command:slack-find-discussions", "slack_search_public"),
    )
    evidence_path = tmp_path / "evidence.md"
    evidence_path.write_text(evidence)

    # Assert
    recorded = evidence_path.read_text()
    assert secret not in recorded
    assert workspace_content not in recorded
    assert "slack_search_public" in recorded


def test_evidence_rejects_non_identity_values() -> None:
    # Arrange
    unsafe_identity = "slack_search_public: private message content"

    # Act / Assert
    with pytest.raises(SmokeFailure, match="unsafe evidence identity"):
        render_evidence("PASS", "SKIPPED", (unsafe_identity,))
