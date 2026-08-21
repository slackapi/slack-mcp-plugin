import json
from pathlib import Path
from typing import cast

OPENCODE_CONFIG = Path(__file__).parents[2] / "opencode.json"


def load_opencode_config() -> dict[str, object]:
    config: object = json.loads(OPENCODE_CONFIG.read_text())
    assert isinstance(config, dict)
    return cast(dict[str, object], config)


class TestOpenCodeConfig:
    def test_native_git_plugin_is_declared(self) -> None:
        config = load_opencode_config()

        plugins = config["plugin"]
        assert plugins == ["slack@git+https://github.com/slackapi/slack-skills-plugin.git"]

    def test_root_config_does_not_duplicate_plugin_mcp_registration(self) -> None:
        config = load_opencode_config()

        assert "mcp" not in config
