import json
import re
from pathlib import Path
from typing import cast

OPENCODE_CONFIG = Path(__file__).parents[2] / "opencode.json"


def load_opencode_config() -> dict[str, object]:
    config: object = json.loads(OPENCODE_CONFIG.read_text())
    assert isinstance(config, dict)
    return cast(dict[str, object], config)


class TestOpenCodeConfig:
    def test_slack_server_endpoint(self) -> None:
        config = load_opencode_config()

        mcp = config["mcp"]
        assert isinstance(mcp, dict)
        slack = mcp["slack"]
        assert isinstance(slack, dict)
        assert slack["type"] == "remote"
        assert slack["url"] == "https://mcp.slack.com/mcp"

    def test_slack_oauth_configuration(self) -> None:
        config = load_opencode_config()

        mcp = config["mcp"]
        assert isinstance(mcp, dict)
        slack = mcp["slack"]
        assert isinstance(slack, dict)
        oauth = slack["oauth"]
        assert isinstance(oauth, dict)
        assert oauth == {
            "clientId": "{env:SLACK_OPENCODE_CLIENT_ID}",
            "redirectUri": "http://127.0.0.1:19876/mcp/oauth/callback",
        }

    def test_slack_configuration_has_only_safe_fields(self) -> None:
        config = load_opencode_config()

        mcp = config["mcp"]
        assert isinstance(mcp, dict)
        slack = mcp["slack"]
        assert isinstance(slack, dict)
        assert set(slack) == {"type", "url", "oauth"}

    def test_slack_configuration_has_no_hardcoded_client_id(self) -> None:
        config = load_opencode_config()

        mcp = config["mcp"]
        assert isinstance(mcp, dict)
        slack = mcp["slack"]
        assert isinstance(slack, dict)
        assert re.search(r"\b\d{10,}\.\d{10,}\b", json.dumps(slack)) is None
