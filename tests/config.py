import json
import os
from collections.abc import Mapping
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the repo root (if present) before reading the environment
load_dotenv(Path(__file__).parent.parent / ".env")


def get_gemini_api_key_pool(environ: Mapping[str, str]) -> list[str]:
    return [environ[name].strip() for name in environ if name.startswith("GEMINI_API_KEY") and environ[name].strip()]


# Filesystem
SKILLS_ROOT = Path(__file__).parent.parent / "skills"

# Plugin namespace (single source of truth: the plugin manifest)
PLUGIN_MANIFEST = Path(__file__).parent.parent / ".claude-plugin" / "plugin.json"
PLUGIN_NAME = json.loads(PLUGIN_MANIFEST.read_text())["name"]

# Skill inventory (single source of truth)
EXPECTED_SKILLS = ("create-slack-app", "block-kit", "slack-api", "slack-cli", "slack-docs")

# Gemini judge model. Any env var whose name starts with GEMINI_API_KEY contributes a
# key to the pool; blank values are skipped so an empty GEMINI_API_KEY= doesn't sneak in.
GEMINI_API_KEY_POOL = get_gemini_api_key_pool(os.environ)
GEMINI_MODEL = os.environ.get("GEMINI_MODEL_NAME", "gemini-3.1-flash-lite")

# Slack MCP server
SLACK_MCP_URL = "https://mcp.slack.com/mcp"
SLACK_MCP_TOKEN = os.environ.get("SLACK_MCP_TOKEN", "")
