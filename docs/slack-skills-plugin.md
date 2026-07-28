# Slack MCP and Skills Plugin

The Slack MCP and Skills Plugin for AI tools bundles together a set of skills that help you develop on the Slack platform with the [Slack MCP Server](/ai/slack-mcp-server). You can use the plugin with Claude Code and Cursor.

Installing the plugin sets up two things:

* **[Skills](#skills)**. Skills supercharge you and your agents when developing Slack apps.
* **[Slack MCP Server connection](/ai/slack-mcp-server)**. The Slack MCP server lets you and your agent interact directly with your Slack workspace, such as searching channels, sending messages, and managing canvases.

The Slack MCP server is configured automatically when the plugin loads. You'll be prompted to authenticate into your Slack workspace via OAuth. Full setup details vary depending on the AI tool you are using.

---

## Installing the plugin

You can install the plugin for Claude Code or for Cursor.

### Installing the plugin for Claude Code

The plugin is published on the [official Claude marketplace](https://claude.com/plugins/slack). You can install the plugin directly from a Claude Code session with a slash command:

```sh
/plugin install slack@claude-plugins-official
```

### Installing the plugin for Cursor

The plugin is published on the [official Cursor Marketplace](https://cursor.com/marketplace/slack). You can install the plugin by clicking the nifty button below:

[![Install MCP Server](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/en-US/install-mcp?name=slack&config=eyJ1cmwiOiJodHRwczovL21jcC5zbGFjay5jb20vbWNwIiwiYXV0aCI6eyJDTElFTlRfSUQiOiIzNjYwNzUzMTkyNjI2Ljg5MDM0NjkyMjg5ODIifX0=")

---

## Using skills {/* #skills */}

Skills are focused sets of instructions and references that your assistant loads when a task calls. The skills load automatically when your prompt calls for them.

Most of the skills work on their own, without a connection to the [Slack MCP server](/ai/slack-mcp-server). The one exception is the `slack-search` skill, which relies on the Slack MCP server to query your workspace.

| Skill | What it helps with | Example prompt |
|-------|--------------------|----------------|
| `block-kit` | Build and validate [Block Kit](/block-kit) layouts for messages, modals, and Home tabs, validating against the `blocks.validate` API method. | _"Build a Block Kit modal with a name field, a dropdown to pick a channel, and a submit button."_ |
| `create-slack-app` | Scaffold a new Slack app or agent with the [Slack CLI](/tools/slack-cli) and [Bolt](/tools#bolt) (JavaScript or Python). | _"Scaffold a new Bolt for JavaScript app that listens for the `app_mention` event."_ |
| `slack-api` | Discover, navigate, and call [Web API methods](/apis/web-api), surfacing info on required scopes, pagination, rate limits, and error handling. | _"Which Web API method posts a message to a channel, and what scopes does it need?"_ |
| `slack-cli` | Create, run, and manage Slack apps from the terminal with the [Slack CLI](/tools/slack-cli), and search the Slack docs from the command line. | _"Run my Slack app locally and tail the logs."_ |
| `slack-messaging` | Compose well-formatted Slack messages using standard markdown. | _"Draft a release announcement message with a bulleted list of changes."_ |
| `slack-search` | Search Slack effectively to find messages, files, channels, and people. Requires a Slack MCP Server connection. | _"Find the channel where we discuss the platform roadmap."_ |