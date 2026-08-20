import json
import re
from pathlib import Path

import pytest

from scripts import opencode as oc

REPO_ROOT = Path(__file__).parents[2]
EXPECTED_SKILLS = {path.parent.name for path in (REPO_ROOT / "skills").glob("*/SKILL.md")}
EXPECTED_COMMANDS = {
    "slack-channel-digest.md",
    "slack-draft-announcement.md",
    "slack-find-discussions.md",
    "slack-standup.md",
    "slack-summarize-channel.md",
}
CLIENT_ID_PATTERN = re.compile(r"\b\d{10,}\.\d{10,}\b")


def config_dir_for(tmp_path: Path) -> Path:
    """A temp global OpenCode config dir (as under $XDG_CONFIG_HOME/opencode)."""
    return tmp_path / "opencode"


def snapshot(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): path.read_text()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def all_text(root: Path) -> str:
    return "\n".join(path.read_text() for path in sorted(root.rglob("*")) if path.is_file())


class TestOpenCodeGlobalInstaller:
    def test_install_creates_expected_skills_commands_and_mcp(self, tmp_path: Path) -> None:
        # Arrange
        config_dir = config_dir_for(tmp_path)

        # Act
        report = oc.install(REPO_ROOT, config_dir)

        # Assert
        assert report.created_skills == EXPECTED_SKILLS
        assert report.created_commands == EXPECTED_COMMANDS
        assert {path.name for path in (config_dir / "skills").iterdir()} == EXPECTED_SKILLS
        assert {path.name for path in (config_dir / "commands").iterdir()} == EXPECTED_COMMANDS

        config = json.loads((config_dir / "opencode.json").read_text())
        assert config["mcp"]["slack"]["type"] == "remote"
        assert config["mcp"]["slack"]["oauth"]["clientId"] == "{env:SLACK_OPENCODE_CLIENT_ID}"

    def test_install_records_ownership_in_manifest(self, tmp_path: Path) -> None:
        # Arrange
        config_dir = config_dir_for(tmp_path)

        # Act
        oc.install(REPO_ROOT, config_dir)
        manifest = json.loads((config_dir / oc.MANIFEST_FILENAME).read_text())

        # Assert
        assert set(manifest["skills"]) == EXPECTED_SKILLS
        assert set(manifest["commands"]) == EXPECTED_COMMANDS
        assert manifest["config"] == {"path": "opencode.json", "created": True}

    def test_install_is_idempotent(self, tmp_path: Path) -> None:
        # Arrange
        config_dir = config_dir_for(tmp_path)
        oc.install(REPO_ROOT, config_dir)
        first = snapshot(config_dir)

        # Act
        report = oc.install(REPO_ROOT, config_dir)

        # Assert
        assert first == snapshot(config_dir)
        assert not report.created_skills
        assert not report.created_commands
        assert report.config_action == "unchanged"

    def test_installed_content_matches_canonical_sources(self, tmp_path: Path) -> None:
        # Arrange
        config_dir = config_dir_for(tmp_path)

        # Act
        oc.install(REPO_ROOT, config_dir)

        # Assert — skills (including nested references like block-kit/references/*)
        for source in sorted((REPO_ROOT / "skills").rglob("*")):
            if source.is_file():
                installed = config_dir / source.relative_to(REPO_ROOT)
                assert installed.read_bytes() == source.read_bytes(), f"{installed} drifted from {source}"
        # Assert — namespaced commands
        for adapter, canonical in oc.COMMAND_ADAPTERS.items():
            installed = config_dir / "commands" / adapter
            assert installed.read_bytes() == (REPO_ROOT / "commands" / canonical).read_bytes()

    def test_no_secrets_or_client_ids_in_installed_artifacts(self, tmp_path: Path) -> None:
        # Arrange
        config_dir = config_dir_for(tmp_path)

        # Act
        oc.install(REPO_ROOT, config_dir)
        installed_text = all_text(config_dir)

        # Assert
        assert CLIENT_ID_PATTERN.search(installed_text) is None
        assert "SLACK_MCP_TOKEN" not in installed_text
        config = json.loads((config_dir / "opencode.json").read_text())
        assert config["mcp"]["slack"]["oauth"]["clientId"] == "{env:SLACK_OPENCODE_CLIENT_ID}"


class TestOpenCodeConfigMerge:
    def test_install_merges_mcp_preserving_other_servers_and_plugins(self, tmp_path: Path) -> None:
        # Arrange
        config_dir = config_dir_for(tmp_path)
        config_dir.mkdir(parents=True)
        preexisting = {
            "$schema": "https://opencode.ai/config.json",
            "mcp": {"other": {"type": "remote", "url": "https://example.com/mcp"}},
            "plugin": ["some-user-plugin"],
        }
        (config_dir / "opencode.json").write_text(json.dumps(preexisting))

        # Act
        report = oc.install(REPO_ROOT, config_dir)

        # Assert
        config = json.loads((config_dir / "opencode.json").read_text())
        assert config["mcp"]["other"] == {"type": "remote", "url": "https://example.com/mcp"}
        assert config["plugin"] == ["some-user-plugin"]
        assert config["mcp"]["slack"]["type"] == "remote"
        assert report.config_action == "merged"

    def test_install_does_not_clobber_preexisting_colliding_skill(self, tmp_path: Path) -> None:
        # Arrange
        config_dir = config_dir_for(tmp_path)
        custom = config_dir / "skills" / "block-kit" / "SKILL.md"
        custom.parent.mkdir(parents=True)
        custom.write_text("---\nname: block-kit\ndescription: my custom skill\n---\n\ncustom body\n")

        # Act
        report = oc.install(REPO_ROOT, config_dir)

        # Assert
        assert "block-kit" in report.collisions
        assert custom.read_text().startswith("---\nname: block-kit\ndescription: my custom skill")
        # The nested reference was not injected into the user's skill dir.
        assert not (config_dir / "skills" / "block-kit" / "references" / "common-patterns.md").exists()

    def test_install_does_not_clobber_preexisting_colliding_command(self, tmp_path: Path) -> None:
        # Arrange
        config_dir = config_dir_for(tmp_path)
        custom = config_dir / "commands" / "slack-standup.md"
        custom.parent.mkdir(parents=True)
        custom.write_text("---\ndescription: my custom command\n---\n\ncustom\n")

        # Act
        report = oc.install(REPO_ROOT, config_dir)

        # Assert
        assert "slack-standup.md" in report.collisions
        assert custom.read_text() == "---\ndescription: my custom command\n---\n\ncustom\n"

    def test_jsonc_config_falls_back_without_rewriting_it(self, tmp_path: Path) -> None:
        # Arrange
        config_dir = config_dir_for(tmp_path)
        config_dir.mkdir(parents=True)
        jsonc = config_dir / "opencode.jsonc"
        jsonc.write_text('{\n  // user comment\n  "mcp": { "other": {} }\n}\n')

        # Act
        report = oc.install(REPO_ROOT, config_dir)

        # Assert
        assert report.config_action == "fallback"
        assert jsonc.read_text().startswith('{\n  // user comment')  # untouched
        fallback = json.loads((config_dir / oc.FALLBACK_CONFIG_FILENAME).read_text())
        assert fallback["mcp"]["slack"]["oauth"]["clientId"] == "{env:SLACK_OPENCODE_CLIENT_ID}"


class TestOpenCodeGlobalUninstall:
    def test_uninstall_removes_only_owned_files_preserving_user_files(self, tmp_path: Path) -> None:
        # Arrange
        config_dir = config_dir_for(tmp_path)
        user_skill = config_dir / "skills" / "my-skill" / "SKILL.md"
        user_command = config_dir / "commands" / "my-command.md"
        user_config = config_dir / "opencode.json"
        user_skill.parent.mkdir(parents=True)
        user_command.parent.mkdir(parents=True)
        user_skill.write_text("---\nname: my-skill\ndescription: mine\n---\n")
        user_command.write_text("---\ndescription: mine\n---\n")
        user_config.write_text(json.dumps({"mcp": {"other": {"type": "remote", "url": "https://example.com"}}}))

        oc.install(REPO_ROOT, config_dir)

        # Act
        oc.uninstall(REPO_ROOT, config_dir)

        # Assert — user content preserved
        assert user_skill.exists()
        assert user_command.exists()
        assert json.loads(user_config.read_text()) == {
            "mcp": {"other": {"type": "remote", "url": "https://example.com"}}
        }
        # Assert — Slack-owned content removed
        assert not (config_dir / "skills" / "block-kit").exists()
        assert not (config_dir / "skills" / "slack-search").exists()
        assert not (config_dir / "commands" / "slack-standup.md").exists()
        assert not (config_dir / oc.MANIFEST_FILENAME).exists()

    def test_uninstall_preserves_user_edited_mcp_slack(self, tmp_path: Path) -> None:
        # Arrange
        config_dir = config_dir_for(tmp_path)
        oc.install(REPO_ROOT, config_dir)
        config_path = config_dir / "opencode.json"
        config = json.loads(config_path.read_text())
        config["mcp"]["slack"]["url"] = "https://user-edited.example.com"
        config_path.write_text(json.dumps(config))

        # Act
        oc.uninstall(REPO_ROOT, config_dir)

        # Assert — the user's edited mcp.slack is left in place
        assert json.loads(config_path.read_text())["mcp"]["slack"]["url"] == "https://user-edited.example.com"

    def test_uninstall_is_a_noop_when_nothing_is_installed(self, tmp_path: Path) -> None:
        # Arrange
        config_dir = config_dir_for(tmp_path)
        config_dir.mkdir(parents=True)

        # Act / Assert — must not raise and must not touch the dir
        oc.uninstall(REPO_ROOT, config_dir)
        assert not (config_dir / oc.MANIFEST_FILENAME).exists()


class TestOpenCodeSync:
    def test_sync_repairs_drift_in_owned_skill(self, tmp_path: Path) -> None:
        # Arrange
        config_dir = config_dir_for(tmp_path)
        oc.install(REPO_ROOT, config_dir)
        drifted = config_dir / "skills" / "block-kit" / "SKILL.md"
        drifted.write_text("---\nname: block-kit\ndescription: drifted\n---\n")

        # Act
        report = oc.sync(REPO_ROOT, config_dir)

        # Assert
        assert "block-kit" in report.updated
        canonical = (REPO_ROOT / "skills" / "block-kit" / "SKILL.md").read_bytes()
        assert drifted.read_bytes() == canonical


class TestOpenCodeConfigDir:
    def test_honors_xdg_config_home(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        # Arrange
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

        # Act
        config_dir = oc.opencode_config_dir()

        # Assert
        assert config_dir == tmp_path / "opencode"

    def test_falls_back_to_home_dot_config(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Arrange
        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)

        # Act
        config_dir = oc.opencode_config_dir()

        # Assert
        assert config_dir.name == "opencode"
        assert str(config_dir).endswith(".config/opencode")
