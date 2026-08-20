# Maintainers Guide

This document describes tools, tasks, and workflows needed to maintain the
`slackapi/slack-skills-plugin` repository. This is a skills plugin
marketplace, so the primary maintenance work is keeping skill content accurate
and plugin versions correct rather than managing build artifacts or package
registries.

## Tools

Maintaining this repo requires:

- **[Claude Code][claude-code]**: the primary development and maintenance tool.
  Most tasks (authoring skills, reviewing diffs) are performed through Claude
  Code rather than traditional CLI tooling.
- **[Cursor][cursor]**: an alternative agentic coding environment. Useful for
  verifying that skills and commands work outside Claude Code before release.
- **[Codex][codex-cli]**: another agentic coding environment. Useful for
  verifying that the skills work outside Claude Code before release.
- **[OpenCode][opencode]**: supports repository-local validation of the Slack
  MCP server, seven skills, and five namespaced commands.
- **Git**: standard version control.
- **[GitHub CLI (`gh`)][gh-cli]**: for creating PRs as drafts and managing
  issues.

### Python (and friends)

We recommend using [pyenv](https://github.com/pyenv/pyenv) for Python runtime management. If you use macOS, follow the following steps:

```sh
brew update
brew install pyenv
```

Install necessary Python runtime for development/testing.

```sh
pyenv install 3.14 # select the latest patch version
pyenv local 3.14

pyenv rehash
```

Then, you can create a new Virtual Environment this way:

```sh
python -m venv .venv
source .venv/bin/activate
```

---

## Local Development & Testing

Before you release (or open a PR), exercise your changes locally: run the test
suite, and load the plugin into Claude Code or Cursor to try the skills and
commands by hand.

### Setup

Run the one-time setup, which creates the virtualenv and installs the test and
lint dependencies (requires Python 3.14+, see above):

```sh
make install
```

The tests read configuration from environment variables. Copy the example file
and fill in what you need. Each variable is documented inline, and the
`Makefile` auto-loads `.env`:

```sh
cp .env.example .env
vim .env
# Set the environment variables
```

### Running the tests

Always use the `make` targets, never invoke `pytest`, `ruff`, `python`, or other tools
directly. The targets manage the virtualenv, load `.env`, and set up the test
dependencies for you.

Run `make help` to list every target with its description (read straight from the
`Makefile`, so it's always current). The ones you'll reach for most:

```sh
make help        # list all targets with their descriptions
make test-unit   # fast structural + frontmatter checks (this is what CI runs)
make test-eval   # LLM-judged skill evaluations (local only)
make test        # both
make lint        # Ruff (Python) + rumdl (Markdown) linter checks
make format      # Auto-format: Ruff for Python, rumdl --fix for Markdown
make typecheck   # Mypy static type checks
```

Markdown linting is powered by [rumdl](https://github.com/rvben/rumdl), a
markdownlint-compatible Rust linter. It validates the plugin's authored
markdown — `skills/`, `commands/`, `README.md`, `AGENTS.md`, and the
contributor-facing `.github/` docs. Rules, disabled checks, and the `include`
list of linted files are configured under `[tool.rumdl]` in `pyproject.toml`;
tune that section when a new file or skill trips a rule that isn't worth
enforcing.

### Testing in Claude Code

Load your local changes into Claude Code for a single session with the
`--plugin-dir` flag:

```sh
claude --plugin-dir ./
```

This loads the `slack` plugin from your checkout: its skills and commands, and
the HTTP MCP server from `.mcp.json`. If you already have the published
`slack` plugin installed, the local copy takes precedence **for that session
only**: nothing is written to your settings, and the installed version is
untouched when you exit. After editing a skill or command, run `/reload-plugins`
inside the session to pick up the change without restarting.

Check the plugin's structure without launching a session:

```sh
claude plugin validate
```

### Testing in Cursor

Install the plugin into your local Cursor, then reload plugins in Cursor to pick
up the changes:

```sh
make cursor-install
```

This copies the plugin into `~/.cursor/plugins/slack@local` and registers it.

To remove it, run `make cursor-uninstall`. (`make clean` also runs the Cursor
uninstall, in addition to removing the virtualenv and other generated files.)

### Testing in Codex

Codex loads plugins only from a marketplace. The repo ships a development marketplace at
`.agents/plugins/marketplace.json` that points at this checkout, so you can add
it as a local marketplace and install the plugin from it.

Register the local marketplace and install the `slack` plugin:

```sh
codex plugin marketplace add ./
codex plugin add slack@slack-dev
```

`codex plugin list` shows the plugin; `codex /plugins` opens the same flow interactively. Start a new Codex session to pick up the plugin, then invoke a skill by name with a `$` mention, for example `$block-kit`.

To remove it

```sh
codex plugin remove slack@slack-dev
codex plugin marketplace remove slack-dev
```

Codex support currently ships only the skills; the hosted MCP server is not yet wired into the Codex surface.

### Testing in OpenCode

OpenCode support is both repository-local and globally installable. The root
`skills/` and `commands/` directories are canonical. Relative symlinks under
`.opencode/` adapt them to OpenCode's native discovery paths for the
repository-local mode; the global installer (below) copies the same content into
`~/.config/opencode/` for use outside a checkout.

#### Global installer

The global installer (`scripts/opencode.py`) mirrors `scripts/cursor.py`:

```sh
make opencode-install   # copy 7 skills + 5 commands + Slack MCP config globally
make opencode-uninstall # remove only what the installer owns
make opencode-sync      # re-copy owned content to match canonical sources
```

`opencode-install` copies the seven canonical skills into
`~/.config/opencode/skills/`, the five namespaced `slack-*` commands into
`~/.config/opencode/commands/`, and merges the Slack MCP entry into
`~/.config/opencode/opencode.json`. It **copies** rather than symlinks: symlinks
into a checkout break the moment the checkout moves or is deleted, whereas
copies are self-contained. The trade-off is that copies drift from canonical as
`skills/` and `commands/` evolve, so the installer records exactly what it owns
in a manifest (`.slack-skills-plugin.json`) and `install`/`sync` re-copy owned
content back to canonical on every run. `uninstall` removes only manifest-owned
files and surgically removes the `mcp.slack` entry, leaving the user's own
skills, commands, and config keys untouched.

Config merge is deliberately conservative. The installer merges into an existing
`opencode.json` without clobbering other servers or plugins. It never rewrites
`opencode.jsonc`, because JSONC comments cannot be safely round-tripped; in that
case (and when `opencode.json` is invalid JSON) it writes a standalone
`opencode.slack.json` for the user to merge by hand. No secret is ever written:
the MCP entry uses `{env:SLACK_OPENCODE_CLIENT_ID}`.

To validate the installer, run the parity, idempotency, collision, uninstall,
and no-secrets checks in `tests/unit/test_opencode_installer.py` via
`make test-unit`, then exercise the real path manually with a scratch config
directory:

```sh
export XDG_CONFIG_HOME="$(mktemp -d)"
make opencode-install
make opencode-install          # idempotent: second run is a no-op
opencode --pure debug skill    # lists the seven canonical skills
opencode --pure debug config   # lists the five slack-* commands
make opencode-uninstall
unset XDG_CONFIG_HOME
```

#### Repository-local validation

First, rerun the credential-free OpenCode 1.18.18 discovery experiment:

```sh
make opencode-symlink-experiment
```

The target must report `PASS` for both skill-directory and command-file symlink
discovery and confirm that protected repository paths were unchanged. It writes
the detailed evidence to
`.tmp/experiments/opencode-1.18.18-symlink-discovery.md`.

Run the structural suite for adapter parity:

```sh
make test-unit
```

Parity validation checks that all seven skill adapters and five namespaced
command adapters resolve to their canonical sources, that nested skill
references remain reachable, and that no unnamespaced OpenCode commands exist.

For a read-only smoke test, use an eligible internal Slack app configured as
described in the README. Enable MCP server access from the app's **App
Assistant** page before authenticating. Export only your local client ID; never
record it in the repository or command output captured in an issue or PR.

```sh
export SLACK_OPENCODE_CLIENT_ID="your-app-client-id"
opencode mcp auth slack
opencode mcp list
opencode --pure debug skill
opencode --pure debug config
opencode
```

Confirm the MCP list reports Slack connected through OAuth, skill discovery
contains the seven canonical names, and command configuration contains the five
`slack-*` names. In the interactive session, invoke a read-only command such as
`/slack-summarize-channel` against a non-sensitive test channel and ask OpenCode
to use `slack-search` without sending messages, adding reactions, creating
channels, or modifying canvases. If MCP access was enabled after an earlier
authorization, reauthorize with `opencode mcp auth slack`; log out first with
`opencode mcp logout slack` if OpenCode retains the old grant.

---

## Versioning

Follow the [conventional commit specification][conv-commits]. PR titles and commit messages use prefixes like `feat:`, `fix:`, `chore:`, `docs:`, etc. First letter after the prefix is lowercase unless it's a proper noun.

### Updating Changesets

This project uses [Changesets](https://github.com/changesets/changesets) to track changes and automate releases.

Each changeset describes a change to the package and its [semver][semver] impact, and a new changeset should be added when updating the package with some change that affects consumers:

```sh
npx changeset add
```

Alternatively, hand-write a file named `.changeset/<anything>.md`, with this format:

```md
---
"slack": minor
---

Add the channel-digest command
```

The frontmatter key is always `"slack"`; the value is the [semver][semver] bump level, like `patch`, `minor`, or `major`. The body becomes the changelog entry, so write it for a reader of the release notes.

Updates to documentation, tests, or CI might not require new entries.

When a PR containing changesets is merged to `main`, a different PR is opened or updated using [changesets/action](https://github.com/changesets/action) which consumes the pending changesets, bumps the package version, and updates the `CHANGELOG` in preparation to release.

### Releases

Releasing can feel intimidating at first, but don't fret! Venture on!

New official package versions are published when the release PR created from changesets is merged. Follow these steps to build confidence:

1. **Run the tests locally**: Before merging the release PR please run all the tests (see [Local Development & Testing](#local-development--testing)), especially the eval ones. If they no longer pass we may need fix it before releasing the changes.

2. **Check GitHub**: Please check if issues or pull requests are still open either decide to postpone the release or save those changes for a future update.

3. **Review the release PR**: Verify that the version bump matches expectations, `CHANGELOG` entries are clear, and CI checks pass.

4. **Merge and approve**: Merge the release PR. It may take up to 24 hours before you see you release in the [Claude Plugins](https://claude.com/plugins/slack) directory.

5. **Communicate the release**: A Slack announcement is posted automatically to the release-announcements channel by `.github/workflows/release.yml` when the release PR is merged and a tag is cut. For broader outreach (e.g. `#tools-bolt` on [Slack Community](https://community.slack.com/)), post manually if desired.

## Everything Else

### CODEOWNERS

Owners are defined in [`.github/CODEOWNERS`](CODEOWNERS). Any PR to this repo automatically requests review from this team.

### Dependabot

Dependabot is configured for GitHub Actions dependencies only (daily cadence).
Patch and minor updates are auto-approved and auto-merged via the
`.github/workflows/dependencies.yml` workflow.

### Issue Triage

- Bug reports about incorrect Block Kit output should be investigated by
  checking whether the relevant live `docs.slack.dev` page has changed.
- Feature requests for new skills should be discussed in the issue before
  implementation begins.
- Labels:
  - `bug`: confirmed defects
  - `enhancement`: feature requests and new functionality
  - `docs`: documentation-only changes
  - `test`: test-only changes
  - `build`: CI, GitHub Actions, and build/compilation processes
  - `chore`: repo structure, required files, release scaffolding, general maintenance
  - `dependencies`: dependency updates (Dependabot applies this automatically)
  - `security`: vulnerability fixes, hardening, and security audit findings
    (apply alongside `bug`/`build`/`dependencies` as appropriate)

---

[claude-code]: https://claude.ai/code
[cursor]: https://cursor.com
[codex-cli]: https://developers.openai.com/codex/cli
[opencode]: https://opencode.ai
[gh-cli]: https://cli.github.com
[conv-commits]: https://www.conventionalcommits.org
[semver]: https://semver.org
