import hashlib
import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

OPENCODE_VERSION = "1.18.18"
REPO_ROOT = Path(__file__).resolve().parent.parent
EVIDENCE_PATH = REPO_ROOT / ".tmp/experiments/opencode-1.18.18-symlink-discovery.md"
PROTECTED_PATHS = (
    "skills",
    "commands",
    "opencode.json",
    ".mcp.json",
    ".cursor-mcp.json",
    ".claude-plugin",
    ".cursor-plugin",
    ".codex-plugin",
)
SKILL_NAME = "synthetic-symlink-skill"
COMMAND_ADAPTER_NAME = "synthetic-symlink-command"
COMMAND_MARKER = "OPENCODE_SYMLINK_COMMAND_MARKER_20260820"


@dataclass(frozen=True)
class Probe:
    label: str
    command: tuple[str, ...]
    cwd: Path
    exit_code: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class Conclusion:
    status: str
    detail: str


def opencode_command(*arguments: str) -> tuple[str, ...]:
    return (
        "npx",
        "--yes",
        f"--package=opencode-ai@{OPENCODE_VERSION}",
        "opencode",
        *arguments,
    )


def isolated_environment(fixture: Path) -> dict[str, str]:
    path = os.environ.get("PATH")
    if not path:
        raise RuntimeError("PATH is required to locate npx")
    runtime = fixture / "runtime"
    values = {
        "HOME": str(runtime / "home"),
        "NO_COLOR": "1",
        "NPM_CONFIG_CACHE": str(runtime / "npm-cache"),
        "NPM_CONFIG_UPDATE_NOTIFIER": "false",
        "OPENCODE_CONFIG_DIR": str(runtime / "opencode-config"),
        "OPENCODE_DISABLE_AUTOUPDATE": "true",
        "OPENCODE_DISABLE_CLAUDE_CODE": "true",
        "OPENCODE_DISABLE_DEFAULT_PLUGINS": "true",
        "OPENCODE_DISABLE_LSP_DOWNLOAD": "true",
        "OPENCODE_DISABLE_MODELS_FETCH": "true",
        "OPENCODE_DISABLE_PRUNE": "true",
        "PATH": path,
        "TERM": "dumb",
        "TMPDIR": str(runtime / "tmp"),
        "XDG_CACHE_HOME": str(runtime / "xdg-cache"),
        "XDG_CONFIG_HOME": str(runtime / "xdg-config"),
        "XDG_DATA_HOME": str(runtime / "xdg-data"),
        "XDG_STATE_HOME": str(runtime / "xdg-state"),
    }
    for directory_key in (
        "HOME",
        "NPM_CONFIG_CACHE",
        "OPENCODE_CONFIG_DIR",
        "TMPDIR",
        "XDG_CACHE_HOME",
        "XDG_CONFIG_HOME",
        "XDG_DATA_HOME",
        "XDG_STATE_HOME",
    ):
        Path(values[directory_key]).mkdir(parents=True, exist_ok=True)
    return values


def run_probe(
    label: str,
    command: tuple[str, ...],
    cwd: Path,
    environment: dict[str, str],
) -> Probe:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
            timeout=180,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return Probe(label, command, cwd, -1, "", f"{type(error).__name__}: {error}")
    return Probe(label, command, cwd, completed.returncode, completed.stdout, completed.stderr)


def run_git_probe(label: str) -> Probe:
    command = (
        "git",
        "diff",
        "--no-ext-diff",
        "--binary",
        "--",
        *PROTECTED_PATHS,
    )
    environment = {"PATH": os.environ.get("PATH", ""), "TERM": "dumb"}
    return run_probe(label, command, REPO_ROOT, environment)


def protected_snapshot() -> dict[str, str]:
    snapshot: dict[str, str] = {}
    for relative in PROTECTED_PATHS:
        root = REPO_ROOT / relative
        paths = (
            [root]
            if not root.is_dir()
            else sorted(path for path in root.rglob("*") if path.is_file())
        )
        for path in paths:
            if path.exists() and path.is_file():
                key = str(path.relative_to(REPO_ROOT))
                snapshot[key] = hashlib.sha256(path.read_bytes()).hexdigest()
    return snapshot


def create_fixture(fixture: Path) -> dict[str, Path]:
    skill = fixture / "canonical/skills" / SKILL_NAME / "SKILL.md"
    command = fixture / "canonical/commands/source-command.md"
    skill_adapter = fixture / ".opencode/skills" / SKILL_NAME
    command_adapter = fixture / ".opencode/commands" / f"{COMMAND_ADAPTER_NAME}.md"
    skill.parent.mkdir(parents=True)
    command.parent.mkdir(parents=True)
    skill_adapter.parent.mkdir(parents=True)
    command_adapter.parent.mkdir(parents=True)
    (fixture / ".git").mkdir()
    (fixture / "opencode.json").write_text("{}\n")
    skill.write_text(
        "---\n"
        f"name: {SKILL_NAME}\n"
        "description: Synthetic skill used only to test project symlink discovery.\n"
        "---\n\n"
        "# Synthetic symlink skill\n"
    )
    command.write_text(
        "---\n"
        "description: Synthetic command used only to test project symlink discovery\n"
        "---\n\n"
        f"{COMMAND_MARKER} $ARGUMENTS\n"
    )
    skill_adapter.symlink_to(Path("../../canonical/skills") / SKILL_NAME, target_is_directory=True)
    command_adapter.symlink_to(Path("../../canonical/commands/source-command.md"))
    return {
        "skill": skill,
        "skill_adapter": skill_adapter,
        "command": command,
        "command_adapter": command_adapter,
    }


def validate_fixture(paths: dict[str, Path]) -> str | None:
    pairs = (
        ("skill_adapter", paths["skill"].parent),
        ("command_adapter", paths["command"]),
    )
    for adapter_name, canonical in pairs:
        adapter = paths[adapter_name]
        if not adapter.is_symlink():
            return f"{adapter} is not a symlink"
        try:
            if not adapter.resolve(strict=True).samefile(canonical):
                return f"{adapter} does not resolve to {canonical}"
        except OSError as error:
            return f"cannot resolve {adapter}: {error}"
    return None


def parse_json_probe(probe: Probe) -> tuple[object | None, str | None]:
    if probe.exit_code != 0:
        return None, f"probe exited with {probe.exit_code}"
    try:
        return json.loads(probe.stdout), None
    except json.JSONDecodeError as error:
        return None, f"stdout was not valid JSON: {error}"


def conclude_skill(probe: Probe) -> Conclusion:
    payload, error = parse_json_probe(probe)
    if error:
        return Conclusion("BLOCKED", error)
    if not isinstance(payload, list):
        return Conclusion("BLOCKED", "skill probe JSON was not a list")
    matches = [item for item in payload if isinstance(item, dict) and item.get("name") == SKILL_NAME]
    if len(matches) > 1:
        return Conclusion("BLOCKED", f"OpenCode returned {len(matches)} entries named {SKILL_NAME}")
    if not matches:
        return Conclusion("NOT DISCOVERED", f"no skill named `{SKILL_NAME}` appeared in debug output")
    return Conclusion("DISCOVERED", f"OpenCode returned exactly one skill named `{SKILL_NAME}`")


def conclude_command(probe: Probe) -> Conclusion:
    payload, error = parse_json_probe(probe)
    if error:
        return Conclusion("BLOCKED", error)
    if not isinstance(payload, dict) or not isinstance(payload.get("command", {}), dict):
        return Conclusion("BLOCKED", "resolved config did not contain a command object")
    commands = payload.get("command", {})
    observed = [name for name, value in commands.items() if COMMAND_MARKER in json.dumps(value)]
    if len(observed) > 1:
        return Conclusion("BLOCKED", f"marker appeared under multiple command names: {observed}")
    if not observed:
        return Conclusion("NOT DISCOVERED", "the synthetic command marker did not appear in resolved config")
    return Conclusion(
        "DISCOVERED",
        f"OpenCode observed command name `{observed[0]}` "
        f"(adapter filename expected `{COMMAND_ADAPTER_NAME}`)",
    )


def fenced(value: str) -> str:
    return f"```text\n{value.rstrip()}\n```" if value else "```text\n<empty>\n```"


def render_probe(probe: Probe) -> str:
    command = subprocess.list2cmdline(probe.command)
    return (
        f"### {probe.label}\n\n"
        f"- Working directory: `{probe.cwd}`\n"
        f"- Command: `{command}`\n"
        f"- Exit code: `{probe.exit_code}`\n\n"
        f"**stdout**\n\n{fenced(probe.stdout)}\n\n"
        f"**stderr**\n\n{fenced(probe.stderr)}\n"
    )


def render_evidence(
    fixture: Path,
    fixture_paths: dict[str, Path],
    probes: list[Probe],
    skill: Conclusion,
    command: Conclusion,
    fixture_error: str | None,
    protected_unchanged: bool,
) -> str:
    path_lines = "\n".join(f"- {name}: `{path}`" for name, path in fixture_paths.items())
    probe_sections = "\n".join(render_probe(probe) for probe in probes)
    overall = "PASS" if skill.status != "BLOCKED" and command.status != "BLOCKED" and protected_unchanged else "BLOCKED"
    fixture_status = str(fixture_error is None).lower()
    fixture_detail = f" — {fixture_error}" if fixture_error else ""
    return f"""# OpenCode {OPENCODE_VERSION} symlink discovery experiment

## Outcome

- Overall: **{overall}**
- Skill-directory symlink: **{skill.status}** — {skill.detail}.
- Command-file symlink: **{command.status}** — {command.detail}.
- Protected repository paths unchanged: **{str(protected_unchanged).lower()}**.

`DISCOVERED` and `NOT DISCOVERED` are emitted only after a successful, parseable probe. Any execution,
version, shape, duplicate-marker, or mutation uncertainty is `BLOCKED`.

## Isolation and fixture paths

- Temporary fixture root: `{fixture}` (removed after the report was written)
- OpenCode package: `opencode-ai@{OPENCODE_VERSION}`
- Credentials inherited: none; the subprocess receives a constructed allowlist environment.
- Network-dependent model and update discovery: disabled with OpenCode environment flags.
- Fixture symlinks valid before probing: **{fixture_status}**{fixture_detail}
{path_lines}

## Protected paths

The before/after SHA-256 snapshot and `git diff --no-ext-diff --binary` output were compared for:
{chr(10).join(f"- `{path}`" for path in PROTECTED_PATHS)}

## Exact probe evidence

{probe_sections}
"""


def main() -> int:
    before_snapshot = protected_snapshot()
    before_diff = run_git_probe("Protected paths: git diff before")
    probes = [before_diff]
    with tempfile.TemporaryDirectory(prefix="opencode-1.18.18-symlink-") as temporary:
        fixture = Path(temporary)
        fixture_paths = create_fixture(fixture)
        fixture_error = validate_fixture(fixture_paths)
        environment = isolated_environment(fixture)
        version = run_probe("OpenCode version", opencode_command("--version"), fixture, environment)
        skill_probe = run_probe("Skill discovery", opencode_command("--pure", "debug", "skill"), fixture, environment)
        command_probe = run_probe(
            "Command discovery",
            opencode_command("--pure", "debug", "config"),
            fixture,
            environment,
        )
        probes.extend((version, skill_probe, command_probe))

        version_ok = version.exit_code == 0 and version.stdout.strip() == OPENCODE_VERSION
        precondition_error = fixture_error or (None if version_ok else "version probe was not exactly 1.18.18")
        skill = conclude_skill(skill_probe) if not precondition_error else Conclusion("BLOCKED", precondition_error)
        command = (
            conclude_command(command_probe)
            if not precondition_error
            else Conclusion("BLOCKED", precondition_error)
        )
        after_diff = run_git_probe("Protected paths: git diff after")
        probes.append(after_diff)
        protected_unchanged = (
            before_snapshot == protected_snapshot()
            and before_diff.exit_code == 0
            and after_diff.exit_code == 0
            and before_diff.stdout == after_diff.stdout
        )
        evidence = render_evidence(
            fixture,
            fixture_paths,
            probes,
            skill,
            command,
            fixture_error,
            protected_unchanged,
        )

    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(evidence)
    print(f"Evidence: {EVIDENCE_PATH}")
    print(f"Skill-directory symlink: {skill.status}")
    print(f"Command-file symlink: {command.status}")
    if skill.status == "BLOCKED" or command.status == "BLOCKED" or not protected_unchanged:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
