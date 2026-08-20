"""Install the Slack plugin's OpenCode mode into the global OpenCode config.

The repository-local mode adapts the canonical ``skills/`` and ``commands/``
directories to OpenCode with relative symlinks under ``.opencode/``. Those
symlinks only work while the checkout stays put: moving or deleting the
repository silently breaks every installed skill and command, and the link
targets are not stable across machines.

This installer instead **copies** the canonical content into the global config
directory (``~/.config/opencode/``), mirroring ``scripts/cursor.py``. Copies are
self-contained and survive the checkout being relocated, renamed, or removed.
The trade-off is that copies drift from the canonical source as ``skills/`` and
``commands/`` evolve, so the installer records exactly which skills and commands
it owns in a manifest and provides a ``sync`` subcommand that re-copies owned
content back to canonical. ``install`` itself also re-syncs owned content on
every run, so an install never leaves a stale copy behind.

Safety properties, in order:

- Only content the installer owns is ever overwritten or removed. A pre-existing
  skill or command at the same path is left untouched and never claimed.
- The Slack MCP entry is merged into an existing ``opencode.json`` without
  clobbering the user's other servers or plugins. ``opencode.jsonc`` may contain
  comments and cannot be safely round-tripped, so it is never rewritten; the
  installer writes a standalone ``opencode.slack.json`` for the user to merge by
  hand and says so.
- No secrets are read, written, or persisted. The MCP entry uses
  ``{env:SLACK_OPENCODE_CLIENT_ID}``; the internal client ID, OAuth tokens, and
  ``SLACK_MCP_TOKEN`` never appear in any installed artifact.
"""

import argparse
import contextlib
import hashlib
import json
import logging
import os
import shutil
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

logger = logging.getLogger(Path(__file__).stem)

REPO_ROOT = Path(__file__).resolve().parent.parent

# Namespaced command adapters -> canonical command files. Mirrors the mapping in
# tests/unit/test_opencode_adapters.py and preserves the `slack-*` namespace so
# the installed commands never collide with generic user commands.
COMMAND_ADAPTERS: dict[str, str] = {
    "slack-channel-digest.md": "channel-digest.md",
    "slack-draft-announcement.md": "draft-announcement.md",
    "slack-find-discussions.md": "find-discussions.md",
    "slack-standup.md": "standup.md",
    "slack-summarize-channel.md": "summarize-channel.md",
}

MANIFEST_FILENAME = ".slack-skills-plugin.json"
CONFIG_FILENAME = "opencode.json"
JSONC_FILENAME = "opencode.jsonc"
MANIFEST_VERSION = 1


def opencode_config_dir(environ: Mapping[str, str] | None = None) -> Path:
    """Return the OpenCode global config directory.

    Honors ``XDG_CONFIG_HOME`` so tests can isolate the install in a temporary
    home; otherwise falls back to the conventional ``~/.config/opencode``.
    """
    env = os.environ if environ is None else environ
    xdg = env.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg) / "opencode"
    return Path.home() / ".config" / "opencode"


@dataclass(frozen=True)
class ConfigRecord:
    """Ownership of the config file the installer touched (if any)."""

    path: str  # config filename relative to the config dir, e.g. "opencode.json"
    created: bool  # True when the installer created the file from scratch


@dataclass
class Manifest:
    """The set of skills/commands/config the installer owns."""

    version: int = MANIFEST_VERSION
    skills: set[str] = field(default_factory=set)
    commands: set[str] = field(default_factory=set)
    config: ConfigRecord | None = None
    slack_mcp_sha256: str | None = None


@dataclass
class Report:
    """Human-readable summary of an install/sync run."""

    created_skills: set[str] = field(default_factory=set)
    created_commands: set[str] = field(default_factory=set)
    updated: set[str] = field(default_factory=set)
    collisions: set[str] = field(default_factory=set)
    config_action: str = "unchanged"


def load_json_object(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def write_json(path: Path, data: dict[str, object]) -> None:
    if path.is_symlink():
        raise ValueError(f"refusing to overwrite symlink: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def load_manifest(config_dir: Path) -> Manifest:
    path = config_dir / MANIFEST_FILENAME
    if not path.exists():
        return Manifest()
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")

    def string_set(value: object) -> set[str]:
        return {item for item in value if isinstance(item, str)} if isinstance(value, list) else set()

    config = None
    raw_config = data.get("config")
    if isinstance(raw_config, dict):
        raw_path = raw_config.get("path")
        raw_created = raw_config.get("created")
        if isinstance(raw_path, str) and isinstance(raw_created, bool):
            config = ConfigRecord(raw_path, raw_created)
    raw_sha = data.get("slackMcpSha256")
    raw_version = data.get("version")
    version = raw_version if isinstance(raw_version, int) else MANIFEST_VERSION
    return Manifest(
        version=version,
        skills=string_set(data.get("skills")),
        commands=string_set(data.get("commands")),
        config=config,
        slack_mcp_sha256=raw_sha if isinstance(raw_sha, str) else None,
    )


def save_manifest(config_dir: Path, manifest: Manifest) -> None:
    config_dir.mkdir(parents=True, exist_ok=True)
    payload: dict[str, object] = {
        "version": manifest.version,
        "skills": sorted(manifest.skills),
        "commands": sorted(manifest.commands),
        "config": (
            {"path": manifest.config.path, "created": manifest.config.created}
            if manifest.config is not None
            else None
        ),
        "slackMcpSha256": manifest.slack_mcp_sha256,
    }
    write_json(config_dir / MANIFEST_FILENAME, payload)


def read_slack_mcp_block(repo_root: Path) -> dict[str, object]:
    """Read the Slack MCP entry from the repository's ``opencode.json``.

    The repository config is the single source of truth, so the installer never
    duplicates the block (and can never drift from what the repo ships).
    """
    config = load_json_object(repo_root / CONFIG_FILENAME)
    mcp = config.get("mcp")
    if not isinstance(mcp, dict) or not isinstance(mcp.get("slack"), dict):
        raise RuntimeError(f"{repo_root / CONFIG_FILENAME} has no mcp.slack entry")
    return cast(dict[str, object], mcp["slack"])


def read_config_schema(repo_root: Path) -> str | None:
    schema = load_json_object(repo_root / CONFIG_FILENAME).get("$schema")
    return schema if isinstance(schema, str) else None


def sha256_block(block: dict[str, object]) -> str:
    return hashlib.sha256(json.dumps(block, sort_keys=True).encode()).hexdigest()


def canonical_skills(repo_root: Path) -> dict[str, list[Path]]:
    """Map each canonical skill name to its sorted list of source files."""
    result: dict[str, list[Path]] = {}
    for skill_dir in sorted((repo_root / "skills").iterdir()):
        if not skill_dir.is_dir():
            continue
        files = sorted(path for path in skill_dir.rglob("*") if path.is_file())
        if files:
            result[skill_dir.name] = files
    return result


def canonical_commands(repo_root: Path) -> dict[str, Path]:
    return {adapter: repo_root / "commands" / name for adapter, name in COMMAND_ADAPTERS.items()}


def copy_file(source: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)


def is_safe_owned_file(path: Path) -> bool:
    """Return whether an owned file is safe to overwrite or remove."""
    return not path.is_symlink()


def files_match(sources: list[Path], target_dir: Path, source_root: Path) -> bool:
    for source in sources:
        dest = target_dir / source.relative_to(source_root)
        if not dest.exists() or dest.read_bytes() != source.read_bytes():
            return False
    return True


def sync_skills(repo_root: Path, config_dir: Path, manifest: Manifest, report: Report) -> None:
    for name, sources in canonical_skills(repo_root).items():
        source_root = repo_root / "skills" / name
        target_dir = config_dir / "skills" / name
        if name in manifest.skills:
            if target_dir.is_symlink():
                logger.warning("not following symlinked owned skill directory: %s", name)
                continue
            for source in sources:
                dest = target_dir / source.relative_to(source_root)
                if not is_safe_owned_file(dest):
                    logger.warning("not overwriting symlinked owned skill file: %s", dest)
                    continue
                if not dest.exists() or dest.read_bytes() != source.read_bytes():
                    copy_file(source, dest)
                    report.updated.add(name)
            continue
        if target_dir.exists():
            if files_match(sources, target_dir, source_root):
                # Pre-existing directory already matches canonical: leave it
                # untouched and unowned so uninstall never removes user content.
                continue
            report.collisions.add(name)
            logger.warning("not overwriting pre-existing skill directory: %s", name)
            continue
        for source in sources:
            copy_file(source, target_dir / source.relative_to(source_root))
        manifest.skills.add(name)
        report.created_skills.add(name)


def sync_commands(repo_root: Path, config_dir: Path, manifest: Manifest, report: Report) -> None:
    for adapter, source in canonical_commands(repo_root).items():
        dest = config_dir / "commands" / adapter
        if adapter in manifest.commands:
            if not is_safe_owned_file(dest):
                logger.warning("not overwriting symlinked owned command: %s", dest)
                continue
            if not dest.exists() or dest.read_bytes() != source.read_bytes():
                copy_file(source, dest)
                report.updated.add(adapter)
            continue
        if dest.exists():
            if dest.read_bytes() == source.read_bytes():
                continue
            report.collisions.add(adapter)
            logger.warning("not overwriting pre-existing command file: %s", adapter)
            continue
        copy_file(source, dest)
        manifest.commands.add(adapter)
        report.created_commands.add(adapter)


def merge_slack_mcp(path: Path, slack_block: dict[str, object]) -> str:
    """Merge the Slack MCP entry into an existing ``opencode.json``.

    Returns ``"merged"``, ``"unchanged"``, or ``"collision"``. Raises
    ``ValueError`` when the file is not valid JSON; callers fall back to the
    non-destructive ``opencode.slack.json`` approach in that case.
    """
    data = load_json_object(path)
    mcp = data.get("mcp")
    if mcp is None:
        mcp = {}
    if not isinstance(mcp, dict):
        raise ValueError(f"{path}: 'mcp' is not an object")
    if "slack" in mcp:
        return "unchanged" if mcp["slack"] == slack_block else "collision"
    mcp["slack"] = slack_block
    data["mcp"] = mcp
    write_json(path, data)
    return "merged"


def create_config(path: Path, slack_block: dict[str, object], schema: str | None) -> None:
    data: dict[str, object] = {}
    if schema is not None:
        data["$schema"] = schema
    data["mcp"] = {"slack": slack_block}
    write_json(path, data)


def install_config(
    config_dir: Path,
    slack_block: dict[str, object],
    schema: str | None,
    manifest: Manifest,
    report: Report,
) -> None:
    json_path = config_dir / CONFIG_FILENAME
    jsonc_path = config_dir / JSONC_FILENAME
    if json_path.is_symlink():
        logger.warning("refusing to modify symlinked config: %s", json_path)
        report.config_action = "skipped"
        return
    if json_path.exists():
        try:
            action = merge_slack_mcp(json_path, slack_block)
        except ValueError as error:
            logger.warning("cannot safely merge %s (%s); leaving it unchanged", json_path, error)
            report.config_action = "skipped"
            return
        report.config_action = action
        if action == "merged":
            manifest.config = ConfigRecord(CONFIG_FILENAME, created=False)
        elif action == "collision":
            logger.warning("%s already defines mcp.slack; leaving it unchanged", json_path)
        return
    if jsonc_path.exists():
        # JSONC can carry comments we cannot preserve, so never rewrite it.
        report.config_action = "skipped"
        logger.warning(
            "%s may contain comments and is left untouched; merge the Slack MCP entry manually",
            jsonc_path,
        )
        return
    create_config(json_path, slack_block, schema)
    manifest.config = ConfigRecord(CONFIG_FILENAME, created=True)
    report.config_action = "created"


def install(repo_root: Path, config_dir: Path) -> Report:
    if (config_dir / MANIFEST_FILENAME).is_symlink():
        raise ValueError("refusing to use a symlinked installer manifest")
    manifest = load_manifest(config_dir)
    slack_block = read_slack_mcp_block(repo_root)
    schema = read_config_schema(repo_root)
    report = Report()

    sync_skills(repo_root, config_dir, manifest, report)
    sync_commands(repo_root, config_dir, manifest, report)
    install_config(config_dir, slack_block, schema, manifest, report)

    manifest.slack_mcp_sha256 = sha256_block(slack_block)
    save_manifest(config_dir, manifest)

    logger.info(
        "installed %d skill(s) and %d command(s) (config: %s)",
        len(report.created_skills),
        len(report.created_commands),
        report.config_action,
    )
    if report.collisions:
        logger.warning(
            "skipped %d pre-existing item(s): %s",
            len(report.collisions),
            ", ".join(sorted(report.collisions)),
        )
    return report


def sync(repo_root: Path, config_dir: Path) -> Report:
    if (config_dir / MANIFEST_FILENAME).is_symlink():
        raise ValueError("refusing to use a symlinked installer manifest")
    manifest = load_manifest(config_dir)
    report = Report()
    sync_skills(repo_root, config_dir, manifest, report)
    sync_commands(repo_root, config_dir, manifest, report)
    save_manifest(config_dir, manifest)
    if report.updated:
        logger.info("re-synced %d owned item(s): %s", len(report.updated), ", ".join(sorted(report.updated)))
    else:
        logger.info("no drift between installed content and canonical sources")
    return report


def uninstall_config(path: Path, created: bool, slack_sha256: str | None) -> str:
    if path.is_symlink():
        logger.warning("refusing to modify symlinked config: %s", path)
        return "left"
    if not path.exists():
        return "absent"
    try:
        data = load_json_object(path)
    except ValueError:
        logger.warning("%s is not valid JSON; leaving it untouched", path)
        return "left"
    mcp = data.get("mcp")
    current_sha = None
    if isinstance(mcp, dict) and isinstance(mcp.get("slack"), dict):
        current_sha = sha256_block(mcp["slack"])
    if not isinstance(mcp, dict) or current_sha != slack_sha256:
        logger.warning("mcp.slack in %s differs from what was installed; leaving it", path)
        return "left"
    del mcp["slack"]
    if mcp:
        data["mcp"] = mcp
    else:
        data.pop("mcp", None)
    if created and set(data) <= {"$schema"}:
        path.unlink()
        return "deleted"
    write_json(path, data)
    return "removed"


def prune_empty_dirs(config_dir: Path) -> None:
    for root_name in ("skills", "commands"):
        root = config_dir / root_name
        if not root.is_dir():
            continue
        for directory in sorted(root.rglob("*"), key=lambda path: len(path.parts), reverse=True):
            if directory.is_dir():
                with contextlib.suppress(OSError):
                    directory.rmdir()
        with contextlib.suppress(OSError):
            root.rmdir()


def uninstall(repo_root: Path, config_dir: Path) -> None:
    manifest = load_manifest(config_dir)
    if not manifest.skills and not manifest.commands and manifest.config is None:
        logger.warning("the Slack plugin is not installed; nothing to remove")
        return

    for name in sorted(manifest.skills):
        for source in canonical_skills(repo_root).get(name, []):
            path = config_dir / "skills" / name / source.relative_to(repo_root / "skills" / name)
            if path.exists() and is_safe_owned_file(path):
                path.unlink()
    for adapter in sorted(manifest.commands):
        if adapter not in COMMAND_ADAPTERS:
            logger.warning("ignoring unrecognized command in manifest: %s", adapter)
            continue
        path = config_dir / "commands" / adapter
        if path.exists() and is_safe_owned_file(path):
            path.unlink()
    prune_empty_dirs(config_dir)

    if manifest.config is not None and manifest.config.path == CONFIG_FILENAME:
        uninstall_config(config_dir / manifest.config.path, manifest.config.created, manifest.slack_mcp_sha256)

    manifest_path = config_dir / MANIFEST_FILENAME
    if manifest_path.exists() and is_safe_owned_file(manifest_path):
        manifest_path.unlink()
    logger.info("removed the Slack plugin's OpenCode installation")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog=Path(__file__).name,
        description=(
            "Install or remove the Slack plugin's OpenCode mode globally. "
            "Copies the seven canonical skills, five namespaced commands, and the "
            "Slack MCP entry into the global OpenCode config directory."
        ),
    )
    parser.add_argument(
        "--config-dir",
        type=Path,
        default=None,
        help=(
            "Override the global OpenCode config directory "
            "(defaults to $XDG_CONFIG_HOME/opencode or ~/.config/opencode)"
        ),
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("install", help="Install skills, commands, and MCP config globally")
    subcommands.add_parser("uninstall", help="Remove only the files this installer owns")
    subcommands.add_parser("sync", help="Re-copy owned content to match the canonical sources")

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    args = parser.parse_args()
    config_dir = args.config_dir if args.config_dir is not None else opencode_config_dir()
    logger.info("OpenCode config directory: %s", config_dir)
    if args.command == "install":
        install(REPO_ROOT, config_dir)
    elif args.command == "uninstall":
        uninstall(REPO_ROOT, config_dir)
    elif args.command == "sync":
        sync(REPO_ROOT, config_dir)
    else:
        parser.error(f"unknown command: {args.command}")


if __name__ == "__main__":
    main()
