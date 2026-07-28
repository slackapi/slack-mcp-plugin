# Slack MCP and Skills Plugin

A [Claude Code][claude-code] and [Cursor][cursor] plugin that brings Slack into your AI tools with a [Slack MCP Server][slack-mcp-docs] and set of Slack skills for both users and developers.

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

The plugin is published on the [official Cursor Marketplace](https://cursor.com/marketplace/slack). Install it directly into Cursor:

[![Install MCP Server](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/en-US/install-mcp?name=slack&config=eyJ1cmwiOiJodHRwczovL21jcC5zbGFjay5jb20vbWNwIiwiYXV0aCI6eyJDTElFTlRfSUQiOiIzNjYwNzUzMTkyNjI2Ljg5MDM0NjkyMjg5ODIifX0%3D)

After install, Cursor surfaces a connect button - use it to authenticate to your Slack workspace.

## Features

### MCP Server

The plugin connects your AI tool to Slack's hosted [MCP server][slack-mcp-docs]:

- **Search** - find messages, files, users, and channels (public and private)
- **Messaging** - send and schedule messages, read channels, follow threads, add reactions
- **Canvas** - create, read, and update canvas documents
- **Users** - read profiles and list channel members

### Skills

Six skills load on demand to handle messaging tasks and developer workflows:

- [`slack:slack-messaging`](skills/slack-messaging/SKILL.md) - composing well-formatted, effective Slack messages
- [`slack:slack-search`](skills/slack-search/SKILL.md) - finding messages, files, channels, and people
- [`slack:slack-api`](skills/slack-api/SKILL.md) - discovering and calling Slack Web API methods
- [`slack:slack-cli`](skills/slack-cli/SKILL.md) - using the [Slack CLI][slack-cli] to create, run, and manage apps
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
[slack-cli]: https://tools.slack.dev/slack-cli
[bolt]: https://tools.slack.dev/bolt-js
[block-kit]: https://app.slack.com/block-kit-builder
