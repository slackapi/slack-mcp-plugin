import json
import re
import subprocess
from pathlib import Path
from typing import Any, cast

REPO_ROOT = Path(__file__).parents[2]
PLUGIN = REPO_ROOT / ".opencode" / "plugins" / "slack.js"
COMMANDS_ROOT = REPO_ROOT / "commands"
EXPECTED_COMMANDS = {
    "slack-channel-digest": "channel-digest.md",
    "slack-draft-announcement": "draft-announcement.md",
    "slack-find-discussions": "find-discussions.md",
    "slack-standup": "standup.md",
    "slack-summarize-channel": "summarize-channel.md",
}
CLIENT_ID = "{env:SLACK_OPENCODE_CLIENT_ID}"
MCP_URL = "https://mcp.slack.com/mcp"
REDIRECT_URI = "http://127.0.0.1:19876/mcp/oauth/callback"
CLIENT_ID_PATTERN = re.compile(r"\b\d{10,}\.\d{10,}\b")
CREDENTIAL_FIELD_PATTERN = re.compile(r"(?i)(?:client[_-]?secret|access[_-]?token|api[_-]?key)\s*[:=]")


def run_hook(config: dict[str, Any]) -> dict[str, Any]:
    """Run the native hook in a subprocess, keeping tests independent of Node globals."""
    runner = f"""
    import {{ SlackPlugin }} from {json.dumps(PLUGIN.as_uri())};
    const config = JSON.parse(process.argv[1]);
    const hooks = await SlackPlugin();
await hooks.config(config);
process.stdout.write(JSON.stringify(config));
"""
    result = subprocess.run(
        ["node", "--input-type=module", "-e", runner, json.dumps(config)],
        check=True,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    return cast(dict[str, Any], json.loads(result.stdout))


def canonical_command(filename: str) -> tuple[str, str]:
    source = (COMMANDS_ROOT / filename).read_text()
    frontmatter, template = source.removeprefix("---\n").split("\n---\n", 1)
    description = next(line.removeprefix("description:").strip() for line in frontmatter.splitlines())
    return description, template.strip()


def test_hook_registers_exactly_the_five_canonical_slack_commands() -> None:
    # Arrange
    initial: dict[str, Any] = {}

    # Act
    config = run_hook(initial)

    # Assert
    assert set(config["command"]) == set(EXPECTED_COMMANDS)


def test_registered_commands_use_canonical_descriptions_and_templates() -> None:
    # Arrange
    initial: dict[str, Any] = {}

    # Act
    commands = run_hook(initial)["command"]

    # Assert
    for name, filename in EXPECTED_COMMANDS.items():
        description, template = canonical_command(filename)
        assert commands[name] == {"description": description, "template": template}


def test_hook_registers_remote_slack_mcp_with_oauth_placeholders() -> None:
    # Arrange
    initial: dict[str, Any] = {}

    # Act
    slack = run_hook(initial)["mcp"]["slack"]

    # Assert
    assert slack == {
        "type": "remote",
        "url": MCP_URL,
        "oauth": {"clientId": CLIENT_ID, "redirectUri": REDIRECT_URI},
    }


def test_existing_slack_mcp_and_command_collisions_are_preserved() -> None:
    # Arrange
    existing_slack = {"type": "remote", "url": "https://user.example/mcp", "enabled": False}
    existing_command = {"template": "user-owned", "description": "custom"}
    initial = {"mcp": {"slack": existing_slack}, "command": {"slack-standup": existing_command}}

    # Act
    config = run_hook(initial)

    # Assert
    assert config["mcp"]["slack"] == existing_slack
    assert config["command"]["slack-standup"] == existing_command


def test_unrelated_configuration_is_preserved_while_missing_entries_are_added() -> None:
    # Arrange
    initial: dict[str, Any] = {
        "$schema": "https://example.test/config.json",
        "model": "user/model",
        "mcp": {"other": {"type": "remote", "url": "https://other.example/mcp"}},
        "command": {"user-command": {"template": "keep me"}},
        "plugin": ["user-plugin"],
    }

    # Act
    config = run_hook(initial)

    # Assert
    assert config["$schema"] == initial["$schema"]
    assert config["model"] == initial["model"]
    assert config["mcp"]["other"] == initial["mcp"]["other"]
    assert config["command"]["user-command"] == initial["command"]["user-command"]
    assert config["plugin"] == initial["plugin"]


def test_repeated_hook_application_is_idempotent() -> None:
    # Arrange
    initial = {"command": {"user-command": {"template": "keep"}}, "mcp": {"other": {}}}
    once = run_hook(initial)

    # Act
    twice = run_hook(once)

    # Assert
    assert twice == once


def test_generated_config_and_plugin_contain_no_hardcoded_credentials() -> None:
    # Arrange
    generated = json.dumps(run_hook({}))
    plugin_source = "\n".join(path.read_text() for path in (REPO_ROOT / ".opencode" / "plugins").glob("*.js"))

    # Act
    inspected_text = generated + plugin_source

    # Assert
    assert CLIENT_ID_PATTERN.search(inspected_text) is None
    assert CREDENTIAL_FIELD_PATTERN.search(inspected_text) is None
    assert "SLACK_MCP_TOKEN" not in inspected_text
    assert '"token"' not in inspected_text.lower()
    assert CLIENT_ID in generated
