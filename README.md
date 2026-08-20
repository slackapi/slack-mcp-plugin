# Slack MCP and Skills Plugin

A [Claude Code][claude-code] and [Cursor][cursor] plugin that brings Slack MCP and skills into those clients. The repository also provides a repository-local OpenCode mode with Slack MCP, skills, and commands.

[![CI Build](https://github.com/slackapi/slack-skills-plugin/actions/workflows/ci-build.yml/badge.svg)](https://github.com/slackapi/slack-skills-plugin/actions/workflows/ci-build.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Installation

### Claude Code

The plugin is published on the [official Claude marketplace](https://claude.com/plugins/slack). Install it from inside Claude Code:

```text
/plugin install slack@claude-plugins-official
```

The Slack MCP server is configured automatically. You'll be prompted to authenticate to your Slack workspace via OAuth on first use.

### Cursor

The plugin is published on the [official Cursor Marketplace](https://cursor.com/marketplace/slack). Install it from inside Cursor:

```text
/add-plugin slack
```

This installs the skills, commands, and MCP server together. You'll be prompted to authenticate to your Slack workspace via OAuth on first use.

### OpenCode

OpenCode 1.18.18 or newer supports this plugin. There are two ways to install it:

- **Global install** (recommended): `make opencode-install` copies the skills,
  commands, and Slack MCP config into `~/.config/opencode/`, so OpenCode picks
  them up from anywhere on your machine.
- **Repository-local**: run OpenCode from inside this checkout.

#### Global install

Clone the repository and run the installer:

```sh
git clone https://github.com/slackapi/slack-skills-plugin.git
cd slack-skills-plugin
make opencode-install
```

The installer copies the seven canonical skills into
`~/.config/opencode/skills/`, the five namespaced commands into
`~/.config/opencode/commands/`, and merges the Slack MCP entry into
`~/.config/opencode/opencode.json`. If `opencode.json` already has other
servers or plugins, only the Slack MCP entry is added — nothing else is touched.
The installer records what it owns, so `make opencode-uninstall` removes exactly
what it installed while leaving your own skills, commands, and config intact.

The installer copies (rather than symlinks) the skills and commands so they keep
working if you later move or delete the checkout. Because copies can drift from
the canonical sources, re-run `make opencode-install` (or `make opencode-sync`)
after updating the checkout to pull in changes.

#### Repository-local (alternative)

Alternatively, run OpenCode from anywhere inside a checkout. OpenCode reads the
root `opencode.json` for Slack MCP and follows the relative symlink adapters
under `.opencode/` to discover the same seven skills and five namespaced
commands. Root `skills/` and `commands/` remain the authored sources.

#### Configure an eligible Slack app

OpenCode currently requires an eligible internal Slack app that you own or
administer. Slack MCP also supports directory-published apps; unlisted apps are
not eligible. Configure an internal app as follows:

1. In **OAuth & Permissions**, add the user scopes required by the Slack MCP
   tools you plan to use:
   - Search: `search:read.public`, `search:read.private`, `search:read.mpim`,
     `search:read.im`, `search:read.files`, `search:read.users`, `files:read`,
     and `emoji:read`.
   - Messages: `chat:write`, `channels:history`, `groups:history`,
     `mpim:history`, `im:history`, and `reactions:write`.
   - Conversations: `channels:write`, `groups:write`, `im:write`,
     `mpim:write`, `channels:read`, `groups:read`, and `mpim:read`.
   - Canvases and profiles: `canvases:read`, `canvases:write`, `users:read`,
     and `users:read.email`.
2. Enable [PKCE][slack-pkce]. This marks the app as a public OAuth client and is
   a one-way operation; disabling it requires contacting Slack support.
3. Register the exact redirect URL
   `http://127.0.0.1:19876/mcp/oauth/callback`.
4. Open the app's **App Assistant** (`app-assistant`) page and enable Slack MCP
   server access **before** authenticating from OpenCode.
5. Ask a workspace admin to approve the app and its requested MCP access.

Slack does not support dynamic client registration, so export the app's client
ID with a placeholder value, authenticate, and verify the connection:

```sh
export SLACK_OPENCODE_CLIENT_ID="your-app-client-id"
opencode mcp auth slack
opencode mcp list
opencode
```

`opencode mcp list` should report Slack connected through OAuth. If you
authenticated before enabling MCP server access, enable it first and then run
`opencode mcp auth slack` again. If OpenCode reuses the earlier authorization,
run `opencode mcp logout slack` before authenticating again.

`SLACK_OPENCODE_CLIENT_ID` intentionally contains a placeholder. No client
secret is needed for this PKCE flow.

#### Use the skills and commands

OpenCode discovers these seven skills:

- `block-kit`
- `create-slack-app`
- `slack-api`
- `slack-cli`
- `slack-docs`
- `slack-messaging`
- `slack-search`

Skills load on demand. For example, prompt OpenCode with "Use the `slack-search`
skill to find discussions about the launch" or "Use the `block-kit` skill to
draft a feedback modal."

OpenCode also discovers exactly five namespaced commands:

- `/slack-channel-digest <channel1, channel2, ...>`
- `/slack-draft-announcement <topic>`
- `/slack-find-discussions <topic>`
- `/slack-standup`
- `/slack-summarize-channel <channel-name>`

For example, run `/slack-summarize-channel engineering` in an OpenCode session.
The `slack-*` namespace avoids collisions with generic project commands.

**Advanced: bearer-token fallback.** If your eligible app already issued a user
token with the required Slack MCP scopes, replace the `oauth` block in your
OpenCode config (`opencode.json` in a checkout, or
`~/.config/opencode/opencode.json` for a global install) with:

```json
"oauth": false,
"headers": {
  "Authorization": "Bearer {env:SLACK_MCP_TOKEN}"
}
```

Set `SLACK_MCP_TOKEN` to that app-issued scoped user token. OpenCode will not run
OAuth or manage token refresh in this mode.

## Features

### MCP Server

The plugin connects your AI tool to Slack's hosted [MCP server][slack-mcp-docs]:

- **Search** - find messages, files, users, and channels (public and private)
- **Messaging** - send and schedule messages, read channels, follow threads, add reactions
- **Canvas** - create, read, and update canvas documents
- **Users** - read profiles and list channel members

### Skills

Seven skills load on demand to handle messaging tasks and developer workflows:

- [`slack:slack-messaging`](skills/slack-messaging/SKILL.md) - composing well-formatted, effective Slack messages
- [`slack:slack-search`](skills/slack-search/SKILL.md) - finding messages, files, channels, and people
- [`slack:slack-api`](skills/slack-api/SKILL.md) - discovering and calling Slack Web API methods
- [`slack:slack-cli`](skills/slack-cli/SKILL.md) - using the [Slack CLI][slack-cli] to create, run, and manage apps
- [`slack:slack-docs`](skills/slack-docs/SKILL.md) - searching and reading current Slack platform documentation
- [`slack:create-slack-app`](skills/create-slack-app/SKILL.md) - building a Slack app or agent with the CLI and [Bolt][bolt]
- [`slack:block-kit`](skills/block-kit/SKILL.md) - building and validating [Block Kit][block-kit] layouts

### Commands

Five slash commands for common Slack workflows:

- `/slack:summarize-channel <channel-name>` - Summarize recent activity in a Slack channel
- `/slack:find-discussions <topic>` - Find discussions about a specific topic across Slack channels
- `/slack:draft-announcement <topic>` - Draft a well-formatted Slack announcement and save it as a draft
- `/slack:standup` - Generate a standup update based on your recent Slack activity
- `/slack:channel-digest <channel1, channel2, ...>` - Get a digest of recent activity across multiple Slack channels

## Usage examples

Once installed, talk to your tool in natural language:

- "Search for messages about the product launch from the last week"
- "Send a message to #general saying the deployment is complete"
- "Summarize the last day of activity in #engineering"
- "Draft an announcement about the new pricing page"
- "Create a new Slack app using Bolt for Python"
- "Build a Block Kit feedback modal with a rating select and a comments field"
- "Validate the Block Kit JSON in ./modal.json"

## Documentation

- [Slack MCP server][slack-mcp-docs]
- [Slack developer docs](https://docs.slack.dev/)
- [Block Kit Builder][block-kit]

## Limitations

- **Workspace admin approval.** Your Slack workspace admin must approve MCP integration before you can authenticate.

## Contributing

We welcome contributions from everyone! Please check out our [contributor's guide](.github/contributing.md) for guidelines on opening issues and pull requests.

Working on the plugin itself? See the [maintainer's guide](.github/maintainers_guide.md) for local development setup.

[claude-code]: https://claude.com/claude-code
[cursor]: https://cursor.com
[slack-mcp-docs]: https://docs.slack.dev/ai/mcp-server/
[slack-pkce]: https://docs.slack.dev/authentication/using-pkce
[slack-cli]: https://tools.slack.dev/slack-cli
[bolt]: https://tools.slack.dev/bolt-js
[block-kit]: https://app.slack.com/block-kit-builder
