import json
import logging
from pathlib import Path

logger = logging.getLogger(Path(__file__).stem)

REPO_ROOT = Path(__file__).resolve().parent.parent

# package.json (committed at the repo root) is the version source of truth; changesets
# bumps it, then this script synchronizes the version out to everywhere else its defined.
PACKAGE_JSON_PATH = REPO_ROOT / "package.json"
CLAUDE_PLUGIN_PATH = REPO_ROOT / ".claude-plugin" / "plugin.json"
CURSOR_PLUGIN_PATH = REPO_ROOT / ".cursor-plugin" / "plugin.json"
CODEX_PLUGIN_PATH = REPO_ROOT / ".codex-plugin" / "plugin.json"


def read_version(package_path: Path) -> str:
    """Return the ``version`` field from ``package.json``."""
    version: str = json.loads(package_path.read_text())["version"]
    return version


def write_version(plugin_path: Path, version: str) -> None:
    """Set the ``version`` field of a JSON plugin manifest."""
    manifest = json.loads(plugin_path.read_text())
    manifest["version"] = version
    plugin_path.write_text(json.dumps(manifest, indent=2) + "\n")
    logger.info(f"Set {plugin_path} version to {version}")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    version = read_version(PACKAGE_JSON_PATH)
    write_version(CLAUDE_PLUGIN_PATH, version)
    write_version(CURSOR_PLUGIN_PATH, version)
    write_version(CODEX_PLUGIN_PATH, version)


if __name__ == "__main__":
    main()
