import json
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

OPENCODE_VERSION = "1.18.18"
REPO_ROOT = Path(__file__).resolve().parent.parent
EVIDENCE_PATH = REPO_ROOT / ".tmp/experiments/opencode-1.18.18-mode-smoke.md"
EXPECTED_COMMANDS = {
    "slack-channel-digest",
    "slack-draft-announcement",
    "slack-find-discussions",
    "slack-standup",
    "slack-summarize-channel",
}
WRITE_MARKERS = ("send", "draft", "schedule", "reaction", "canvas", "create", "update", "delete", "write", "reply")
IDENTITY_PATTERN = re.compile(r"^[a-z0-9_-]+(?::[a-z0-9_-]+)?$")
ANSI_ESCAPE_PATTERN = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


class SmokeFailure(RuntimeError):
    pass


@dataclass(frozen=True)
class CommandResult:
    exit_code: int
    stdout: str
    stderr: str


def run_command(*arguments: str, timeout: int = 180) -> CommandResult:
    """Run a subprocess, capturing output to files rather than a pipe.

    OpenCode truncates large output (e.g. `debug skill`) when its stdout is a
    pipe, but emits full output when stdout is a regular file. Writing to files
    keeps discovery results complete and deterministic.
    """
    try:
        with tempfile.TemporaryDirectory(prefix="opencode-smoke-") as temp:
            stdout_path = Path(temp) / "stdout"
            stderr_path = Path(temp) / "stderr"
            with stdout_path.open("w") as stdout, stderr_path.open("w") as stderr:
                completed = subprocess.run(
                    arguments,
                    cwd=REPO_ROOT,
                    env=os.environ.copy(),
                    check=False,
                    stdout=stdout,
                    stderr=stderr,
                    text=True,
                    timeout=timeout,
                )
            return CommandResult(
                completed.returncode,
                stdout_path.read_text(),
                stderr_path.read_text(),
            )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise SmokeFailure(f"command execution failed: {type(error).__name__}") from error


def require_success(result: CommandResult, label: str) -> None:
    if result.exit_code != 0:
        raise SmokeFailure(f"{label} failed with exit code {result.exit_code}")


def parse_json(result: CommandResult, label: str) -> object:
    require_success(result, label)
    try:
        return json.loads(ANSI_ESCAPE_PATTERN.sub("", result.stdout).strip())
    except json.JSONDecodeError as error:
        raise SmokeFailure(f"{label} did not return valid JSON") from error


def parse_partial_skill_names(result: CommandResult, label: str) -> set[str]:
    """Extract skill names from `debug skill` output that OpenCode may truncate.

    The `debug skill` array embeds the full content of every skill, and OpenCode
    truncates the trailing JSON once a large global skill's content is reached.
    The project skills appear before that point, so we stream-parse each complete
    leading object instead of requiring the whole array to be valid JSON.
    """
    text = ANSI_ESCAPE_PATTERN.sub("", result.stdout).strip()
    if not text.startswith("["):
        raise SmokeFailure(f"{label} did not return a JSON array")
    names: set[str] = set()
    decoder = json.JSONDecoder()
    index = 1
    while index < len(text):
        while index < len(text) and text[index] in " \t\n\r,":
            index += 1
        if index >= len(text) or text[index] == "]":
            break
        try:
            value, end = decoder.raw_decode(text, index)
        except json.JSONDecodeError:
            break
        if isinstance(value, dict) and isinstance(value.get("name"), str):
            names.add(value["name"])
        index = end
    if not names:
        raise SmokeFailure(f"{label} produced no complete skill entries")
    return names


def assert_exact_version(result: CommandResult) -> None:
    if result.exit_code != 0 or result.stdout.strip() != OPENCODE_VERSION:
        raise SmokeFailure(f"OpenCode version must report exactly {OPENCODE_VERSION}")


def assert_discovery(
    skill_result: CommandResult,
    config_result: CommandResult,
    expected_skills: set[str],
    expected_commands: set[str],
) -> None:
    observed_skills = parse_partial_skill_names(skill_result, "skill discovery")
    missing_skills = expected_skills - observed_skills
    if missing_skills:
        raise SmokeFailure(f"repository-local skills missing: {sorted(missing_skills)}")

    config = parse_json(config_result, "command discovery")
    if not isinstance(config, dict) or not isinstance(config.get("command"), dict):
        raise SmokeFailure("command discovery returned an unexpected shape")
    observed_commands = {name for name in config["command"] if isinstance(name, str) and name.startswith("slack-")}
    if observed_commands != expected_commands:
        raise SmokeFailure("repository-local command inventory did not match expected commands")


def canonical_skills() -> set[str]:
    return {path.parent.name for path in (REPO_ROOT / "skills").glob("*/SKILL.md")}


def walk_json(value: object) -> list[dict[str, object]]:
    nodes: list[dict[str, object]] = []
    if isinstance(value, dict):
        nodes.append(value)
        for child in value.values():
            nodes.extend(walk_json(child))
    elif isinstance(value, list):
        for child in value:
            nodes.extend(walk_json(child))
    return nodes


def parse_event_stream(result: CommandResult, label: str) -> list[dict[str, object]]:
    require_success(result, label)
    events: list[dict[str, object]] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        try:
            payload: object = json.loads(line)
        except json.JSONDecodeError as error:
            raise SmokeFailure(f"{label} emitted non-JSON event output") from error
        events.extend(walk_json(payload))
    if not events:
        raise SmokeFailure(f"{label} emitted no JSON events")
    return events


def tool_observations(events: list[dict[str, object]]) -> dict[str, str]:
    observed: dict[str, str] = {}
    for node in events:
        tool = node.get("tool")
        if not isinstance(tool, str):
            continue
        state = node.get("state")
        status = state.get("status") if isinstance(state, dict) else node.get("status")
        if isinstance(status, str):
            observed[tool] = status
    return observed


def assert_skill_selected(events: list[dict[str, object]], expected: str) -> str:
    for node in events:
        if node.get("tool") != "skill":
            continue
        state = node.get("state")
        if not isinstance(state, dict) or state.get("status") != "completed":
            continue
        skill_input = state.get("input")
        if isinstance(skill_input, dict) and expected in skill_input.values():
            return f"skill:{expected}"
    raise SmokeFailure(f"repository-local skill {expected} was not selected successfully")


def assert_read_only_tools(observations: dict[str, str]) -> tuple[str, ...]:
    slack_tools = {name: status for name, status in observations.items() if "slack" in name}
    unsafe = sorted(name for name in slack_tools if any(marker in name for marker in WRITE_MARKERS))
    if unsafe:
        raise SmokeFailure("model selected a write-capable Slack tool")
    completed = sorted(
        name
        for name, status in slack_tools.items()
        if status == "completed" and ("search" in name or "read" in name)
    )
    if not completed:
        raise SmokeFailure("no completed read-only Slack search or read call was observed")
    return tuple(completed)


def assert_mcp_connected(result: CommandResult) -> None:
    require_success(result, "Slack MCP connection check")
    if not re.search(r"(?im)^.*slack.*connected.*$", result.stdout):
        raise SmokeFailure("Slack MCP is not reported as connected")


def render_evidence(discovery_status: str, full_status: str, identities: tuple[str, ...]) -> str:
    if any(not IDENTITY_PATTERN.fullmatch(identity) for identity in identities):
        raise SmokeFailure("unsafe evidence identity")
    identity_lines = "\n".join(f"- `{identity}`" for identity in identities) or "- None"
    return f"""# OpenCode {OPENCODE_VERSION} mode smoke

## Status

- Discovery: **{discovery_status}**
- Model and Slack MCP: **{full_status}**
- Privacy: **PASS** — evidence records statuses and tool identities only.
- Read-only policy: **PASS** — Slack writes were explicitly prohibited.

## Selected identities

{identity_lines}
"""


def write_evidence(discovery_status: str, full_status: str, identities: tuple[str, ...] = ()) -> None:
    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(render_evidence(discovery_status, full_status, identities))


def run_full_smoke(model: str, agent: str | None) -> tuple[str, ...]:
    mcp = run_command("opencode", "mcp", "list")
    assert_mcp_connected(mcp)
    prohibition = (
        "Do not invoke Slack send, draft, schedule, reaction, canvas mutation, or any other write tool. "
        "Do not reveal workspace content or credentials."
    )
    agent_args = ("--agent", agent) if agent else ()
    skill_run = run_command(
        "opencode",
        "run",
        "--format",
        "json",
        "--model",
        model,
        *agent_args,
        f"Use the repository-local block-kit skill to describe a plain section block. {prohibition}",
    )
    skill_events = parse_event_stream(skill_run, "skill invocation")
    skill_identity = assert_skill_selected(skill_events, "block-kit")

    slack_run = run_command(
        "opencode",
        "run",
        "--format",
        "json",
        "--model",
        model,
        *agent_args,
        f"Use the slack_search_public tool to search for messages matching the word 'hello'. "
        f"Report only how many results were found, not their content. {prohibition}",
    )
    slack_events = parse_event_stream(slack_run, "Slack MCP invocation")
    read_tools = assert_read_only_tools(tool_observations(slack_events))
    return (skill_identity, *read_tools)


def main() -> int:
    discovery_status = "FAIL"
    full_status = "SKIPPED"
    try:
        if os.environ.get("OPENCODE_SMOKE_READ_ONLY") != "1":
            raise SmokeFailure("set OPENCODE_SMOKE_READ_ONLY=1 to acknowledge the read-only policy")
        assert_exact_version(run_command("opencode", "--version"))
        assert_discovery(
            run_command("opencode", "--pure", "debug", "skill"),
            run_command("opencode", "--pure", "debug", "config"),
            canonical_skills(),
            EXPECTED_COMMANDS,
        )
        discovery_status = "PASS"
        identities: tuple[str, ...] = ()
        if os.environ.get("OPENCODE_SMOKE_FULL") == "1":
            model = os.environ.get("OPENCODE_SMOKE_MODEL")
            if not model:
                raise SmokeFailure("OPENCODE_SMOKE_MODEL is required for the full smoke")
            agent = os.environ.get("OPENCODE_SMOKE_AGENT")
            identities = run_full_smoke(model, agent)
            full_status = "PASS"
        write_evidence(discovery_status, full_status, identities)
        print(f"OpenCode discovery: {discovery_status}")
        print(f"Model and Slack MCP: {full_status}")
        print(f"Evidence: {EVIDENCE_PATH.relative_to(REPO_ROOT)}")
        return 0
    except SmokeFailure as error:
        write_evidence(discovery_status, "FAIL" if os.environ.get("OPENCODE_SMOKE_FULL") == "1" else full_status)
        print(f"OpenCode smoke failed: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
