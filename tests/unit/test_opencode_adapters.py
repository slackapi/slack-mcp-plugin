import os
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
SKILLS_ROOT = REPO_ROOT / "skills"
COMMANDS_ROOT = REPO_ROOT / "commands"
OPENCODE_SKILLS_ROOT = REPO_ROOT / ".opencode" / "skills"
OPENCODE_COMMANDS_ROOT = REPO_ROOT / ".opencode" / "commands"

COMMAND_ADAPTERS = {
    "slack-channel-digest.md": "channel-digest.md",
    "slack-draft-announcement.md": "draft-announcement.md",
    "slack-find-discussions.md": "find-discussions.md",
    "slack-standup.md": "standup.md",
    "slack-summarize-channel.md": "summarize-channel.md",
}


def split_frontmatter_and_body(content: str) -> tuple[str, str]:
    assert content.startswith("---\n"), "Command must start with YAML frontmatter"
    frontmatter, body = content.removeprefix("---\n").split("\n---\n", 1)
    return frontmatter, body


class TestOpenCodeSkillAdapters:
    def test_inventory_exactly_matches_canonical_skills(self) -> None:
        # Arrange
        canonical_names = {path.parent.name for path in SKILLS_ROOT.glob("*/SKILL.md")}

        # Act
        adapter_names = {path.name for path in OPENCODE_SKILLS_ROOT.iterdir()}

        # Assert
        assert adapter_names == canonical_names

    def test_adapters_are_safe_relative_links_to_canonical_skills(self) -> None:
        # Arrange
        canonical_names = {path.parent.name for path in SKILLS_ROOT.glob("*/SKILL.md")}

        # Act
        links = [(OPENCODE_SKILLS_ROOT / name, SKILLS_ROOT / name) for name in canonical_names]

        # Assert
        for adapter, canonical in links:
            assert adapter.is_symlink(), f"{adapter} must be a symlink"
            assert not Path(os.readlink(adapter)).is_absolute(), f"{adapter} must use a relative target"
            assert adapter.exists(), f"{adapter} is a broken symlink"
            assert adapter.resolve(strict=True) == canonical.resolve(strict=True), (
                f"{adapter} must resolve only to {canonical}"
            )
            assert adapter.resolve(strict=True).is_relative_to(SKILLS_ROOT.resolve(strict=True)), (
                f"{adapter} escapes the canonical skills root"
            )

    def test_skill_files_and_nested_references_resolve_to_canonical_content(self) -> None:
        # Arrange
        canonical_files = [path for path in SKILLS_ROOT.rglob("*") if path.is_file()]

        # Act
        adapted_files = [(OPENCODE_SKILLS_ROOT / path.relative_to(SKILLS_ROOT), path) for path in canonical_files]

        # Assert
        for adapter_file, canonical_file in adapted_files:
            assert adapter_file.resolve(strict=True) == canonical_file.resolve(strict=True)
            assert adapter_file.read_bytes() == canonical_file.read_bytes()


class TestOpenCodeCommandAdapters:
    def test_inventory_is_exactly_the_five_namespaced_commands(self) -> None:
        # Arrange
        expected_names = set(COMMAND_ADAPTERS)

        # Act
        adapter_names = {path.name for path in OPENCODE_COMMANDS_ROOT.iterdir()}
        canonical_names = {path.name for path in COMMANDS_ROOT.glob("*.md")}

        # Assert
        assert adapter_names == expected_names
        assert canonical_names == set(COMMAND_ADAPTERS.values())

    def test_commands_are_safe_relative_links_to_their_canonical_files(self) -> None:
        # Arrange
        links = [
            (OPENCODE_COMMANDS_ROOT / adapter_name, COMMANDS_ROOT / canonical_name)
            for adapter_name, canonical_name in COMMAND_ADAPTERS.items()
        ]

        # Act
        resolved_links = [
            (adapter, canonical, Path(os.readlink(adapter)), adapter.resolve(strict=True))
            for adapter, canonical in links
        ]

        # Assert
        for adapter, canonical, target, resolved in resolved_links:
            assert adapter.is_symlink(), f"{adapter} must be a symlink"
            assert not target.is_absolute(), f"{adapter} must use a relative target"
            assert adapter.exists(), f"{adapter} is a broken symlink"
            assert resolved == canonical.resolve(strict=True), f"{adapter} must resolve only to {canonical}"
            assert resolved.is_relative_to(COMMANDS_ROOT.resolve(strict=True)), (
                f"{adapter} escapes the canonical commands root"
            )

    def test_command_frontmatter_body_and_arguments_match_canonical_content(self) -> None:
        # Arrange
        command_pairs = [
            (OPENCODE_COMMANDS_ROOT / adapter_name, COMMANDS_ROOT / canonical_name)
            for adapter_name, canonical_name in COMMAND_ADAPTERS.items()
        ]

        # Act
        contents = [(adapter.read_text(), canonical.read_text()) for adapter, canonical in command_pairs]

        # Assert
        for adapted_content, canonical_content in contents:
            assert split_frontmatter_and_body(adapted_content) == split_frontmatter_and_body(canonical_content)
            assert adapted_content.count("$ARGUMENTS") == canonical_content.count("$ARGUMENTS")


def test_canonical_roots_do_not_point_back_into_opencode() -> None:
    # Arrange
    canonical_roots = (SKILLS_ROOT, COMMANDS_ROOT)
    opencode_root = (REPO_ROOT / ".opencode").resolve(strict=True)

    # Act
    canonical_paths = [path for root in canonical_roots for path in root.rglob("*")]

    # Assert
    for root in canonical_roots:
        assert not root.is_symlink(), f"{root} must remain the canonical directory"
    for path in canonical_paths:
        assert not path.resolve(strict=True).is_relative_to(opencode_root), f"{path} points back into .opencode"
