import json
import subprocess
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).parents[2]
CANONICAL_SKILLS_ROOT = REPO_ROOT / "skills"
EXPECTED_SKILLS = {
    "block-kit",
    "create-slack-app",
    "slack-api",
    "slack-cli",
    "slack-docs",
    "slack-messaging",
    "slack-search",
    "test-slack-app",
}


def run_node(source: str) -> Any:
    result = subprocess.run(
        ["node", "--input-type=module", "--eval", source],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def run_plugin_config(initial_config: dict[str, object]) -> dict[str, object]:
    serialized_config = json.dumps(initial_config)
    output = run_node(
        f"""import {{ SlackPlugin }} from "./.opencode/plugins/slack.js";
const input = {serialized_config};
const plugin = await SlackPlugin();
await plugin.config(input);
console.log(JSON.stringify(input));"""
    )
    assert isinstance(output, dict)
    return output


class TestOpenCodePluginSkills:
    def test_hook_path_discovers_exactly_the_canonical_skills(self) -> None:
        # Arrange
        initial_config: dict[str, object] = {"other": {"keep": True}}

        # Act
        config = run_plugin_config(initial_config)
        skills = config["skills"]
        assert isinstance(skills, dict)
        paths = skills["paths"]
        assert isinstance(paths, list)
        skill_root = Path(paths[0])

        # Assert
        discovered = {path.parent.name for path in skill_root.glob("*/SKILL.md")}
        assert discovered == EXPECTED_SKILLS
        assert len(discovered) == 8
        assert skill_root.resolve() == CANONICAL_SKILLS_ROOT.resolve()

    def test_runtime_skills_boundary_adds_missing_paths_without_requiring_public_sdk_field(self) -> None:
        # Arrange
        initial_config = {"command": {"user-command": {"template": "keep"}}}

        # Act
        output = run_node(
            """import { registerCanonicalSkills } from "./.opencode/plugins/skill-compatibility.js";
const input = { command: { "user-command": { template: "keep" } } };
const changed = registerCanonicalSkills(input);
console.log(JSON.stringify({ changed, input }));"""
        )
        assert isinstance(output, dict)

        # Assert
        assert output["changed"] is True
        assert output["input"]["command"] == initial_config["command"]
        assert len(output["input"]["skills"]["paths"]) == 1

    def test_runtime_skills_boundary_ignores_incompatible_shapes(self) -> None:
        # Arrange
        output = run_node(
            """import { registerCanonicalSkills } from "./.opencode/plugins/skill-compatibility.js";
const inputs = [
  { skills: null },
  { skills: { paths: "not-an-array" } },
  Object.freeze({}),
];
const results = inputs.map((input) => ({ changed: registerCanonicalSkills(input), input }));
console.log(JSON.stringify(results));"""
        )

        # Act
        assert isinstance(output, list)

        # Assert
        assert [result["changed"] for result in output] == [False, False, False]
        assert output[0]["input"] == {"skills": None}
        assert output[1]["input"] == {"skills": {"paths": "not-an-array"}}
        assert output[2]["input"] == {}

    def test_repeated_hook_execution_is_idempotent_and_preserves_unrelated_config(self) -> None:
        # Arrange
        output = run_node(
            """import { SlackPlugin } from "./.opencode/plugins/slack.js";
const input = {
  skills: { paths: ["/user/skills"] },
  command: { "user-command": { template: "keep" } },
  mcp: { other: { type: "remote", url: "https://example.invalid/mcp" } },
};
const plugin = await SlackPlugin();
await plugin.config(input);
const once = JSON.parse(JSON.stringify(input));
await plugin.config(input);
console.log(JSON.stringify({ once, twice: input }));"""
        )

        # Act
        assert isinstance(output, dict)

        # Assert
        assert output["twice"] == output["once"]
        assert output["twice"]["skills"]["paths"] == ["/user/skills", str(CANONICAL_SKILLS_ROOT)]
        assert output["twice"]["command"]["user-command"] == {"template": "keep"}
        assert output["twice"]["mcp"]["other"] == {
            "type": "remote",
            "url": "https://example.invalid/mcp",
        }

    def test_hook_does_not_use_obsolete_opencode_symlink_adapter_root(self) -> None:
        # Arrange
        config = run_plugin_config({})
        skills = config["skills"]
        assert isinstance(skills, dict)
        paths = skills["paths"]
        assert isinstance(paths, list)

        # Act
        registered_root = Path(paths[0]).resolve()

        # Assert
        assert registered_root == CANONICAL_SKILLS_ROOT.resolve()
        assert ".opencode" not in registered_root.parts
        assert all(not skill.is_symlink() for skill in registered_root.glob("*/SKILL.md"))
