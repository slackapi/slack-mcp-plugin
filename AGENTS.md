# Slack Plugin

This plugin integrates Slack with Ai tools, providing tools to search, read, and send messages in Slack. It also offers useful skills for users and developers.

## Commands

- `/slack:summarize-channel <channel-name>`: Summarize recent activity in a Slack channel
- `/slack:find-discussions <topic>`: Find discussions about a specific topic across Slack channels
- `/slack:draft-announcement <topic>`: Draft a well-formatted Slack announcement and save it as a draft
- `/slack:standup`: Generate a standup update based on your recent Slack activity
- `/slack:channel-digest <channel1, channel2, ...>`: Get a digest of recent activity across multiple Slack channels

## Development Commands

Requires Python 3.14+. Run `make install` before first use to set up the virtual environment and test dependencies.

**Always use the make targets rather than invoking python, pytest, ruff, or other tools directly.** The targets manage the virtualenv for you; running the underlying tools by hand skips that setup and will behave differently. If a `make` command is broken or missing something you need, fix the `Makefile` rather than working around it with the raw command.

Run `make help` for the full list of targets and what each does. The common ones:

| Command | Purpose |
|---------|---------|
| `make help` | Show this help message |
| `make install` | Set up everything (venv + deps) |
| `make lint` | Run linter checks (ruff for Python, rumdl for Markdown) |
| `make format` | Auto-format code (ruff for Python, rumdl for Markdown) |
| `make typecheck` | Run mypy static type checks |
| `make test-unit` | Run structural/unit validation tests |
| `make test-eval` | Run LLM-judged tests (DeepEval against Gemini) |
| `make test` | Run all tests (unit + eval) |
| `make clean` | Remove virtualenv and local Cursor install |
| `make cursor-install` | Install this plugin into a local Cursor for development |
| `make cursor-uninstall` | Uninstall this plugin from the local Cursor install |

See the [maintainers guide](.github/maintainers_guide.md#local-development--testing) for local development and testing setup.

Eval tests (`make test-eval`) need a Gemini API key and, for the MCP tool-selection test, `SLACK_MCP_TOKEN`. Copy `.env.example` to `.env` and fill in values; each variable is documented inline there, and the `Makefile` auto-loads `.env`.

## Cross-Skill References

When one `SKILL.md` references another skill (e.g., to delegate a step instead of duplicating content), follow these rules:

- Use the backticked `plugin:skill` form, e.g. `` `slack:slack-cli` ``.
- When pointing at a specific step, include the step's heading text, not just the number, so references survive future reordering.
- Add a sentence of prose explaining what the referenced section does and why you're delegating to it.
- Don't use markdown anchor links (`[text](#step-1)`), `@`-include syntax (`@path/to/SKILL.md`), or bare file paths: none are idiomatic in installed skills, and `@`-includes force-load context.

See `skills/create-slack-app/SKILL.md` Step 1a for an example.

## Testing

Two test layers validate skills:

1. **Unit** (`tests/unit/`): validates frontmatter fields, naming, and markdown structure. Fast, runs in CI on every PR.
2. **Eval** (`tests/eval/`): LLM-judged tests that use a Gemini model. `tests/eval/test_tool_selection.py` asks the model to pick the expected tool/skill for each of a set of prompts. Because Gemini's free tier caps at 15 requests/minute, the test sleeps ~5s between scenarios (see its `teardown_method`) to stay under the limit.

To add an eval scenario, append a `Scenario` (prompt + expected tool) to `SCENARIOS` in `tests/eval/test_tool_selection.py`.

## CI

GitHub Actions (`.github/workflows/ci-build.yml`) gates every PR with:

- **Lint**: `make lint`
- **Typecheck**: `make typecheck`
- **Test**: `make test-unit`
- **Eval**: `make test-eval`

The eval job reads the `GEMINI_API_KEY_*` (e.g. `GEMINI_API_KEY_BOB`, `GEMINI_API_KEY_MIC`) and `SLACK_MCP_TOKEN` repository secrets; it skips on PRs from forks, which don't receive secrets. The workflow also runs nightly on a schedule, and a `notifications` job posts to Slack (via `SLACK_REGRESSION_FAILURES_WEBHOOK_URL`) when a job fails on `main`.

## Releasing

Releases are automated and run in CI: **you never run a release yourself.** Your only release-related task is adding a changeset when a PR makes a user-facing change.

See the [maintainers guide](.github/maintainers_guide.md#updating-changesets) for the format.

Everything after that is handled by [changesets](https://github.com/changesets/changesets) and `scripts/changeset_version.sh`: merging to `main` opens a "chore: release" PR, and merging that PR publishes the release.
