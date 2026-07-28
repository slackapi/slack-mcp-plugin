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
[gh-cli]: https://cli.github.com
[conv-commits]: https://www.conventionalcommits.org
[semver]: https://semver.org
