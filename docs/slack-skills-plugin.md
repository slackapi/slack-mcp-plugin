# Slack MCP and Skills Plugin

The Slack MCP and Skills Plugin for AI tools bundles together a set of skills that help you develop on the Slack platform with the [Slack MCP Server](/ai/slack-mcp-server). You can use the plugin with Claude Code, Cursor, and Codex, and you can install the skills on their own into dozens of other agents.

Installing the plugin sets up two things:

* **[Skills](#skills)**. Skills supercharge you and your agents when developing Slack apps.
* **[Slack MCP Server connection](/ai/slack-mcp-server)**. The Slack MCP server lets you and your agent interact directly with your Slack workspace, such as searching channels, sending messages, and managing canvases.

The Slack MCP server is configured automatically when the plugin loads. You'll be prompted to authenticate into your Slack workspace via OAuth. Full setup details vary depending on the AI tool you are using.

On Codex, the plugin installs the skills only. The Slack MCP server is not yet available on that surface, so there is no OAuth prompt.

---

## Installing the plugin

You can install the plugin for Claude Code, Cursor, or Codex, or install the skills on their own for another agent.

### Installing the plugin for Claude Code

The plugin is published on the [official Claude marketplace](https://claude.com/plugins/slack). You can install the plugin directly from a Claude Code session with a slash command:

```sh
/plugin install slack@claude-plugins-official
```

### Installing the plugin for Cursor

The plugin is published on the [official Cursor Marketplace](https://cursor.com/marketplace/slack). You can install the plugin directly from a Cursor Agent chat with a slash command:

```sh
/add-plugin slack
```

Alternatively, search for "slack" in the Cursor plugin marketplace. This installs the skills, and MCP server together, and prompts OAuth to your Slack workspace on first use.

### Installing the plugin for Codex

The plugin is published as a marketplace in its [GitHub repository](https://github.com/slackapi/slack-skills-plugin). Add the marketplace, then install the plugin:

```sh
codex plugin marketplace add slackapi/slack-skills-plugin
codex plugin add slack@slack
```

This installs the skills only. Because the Slack MCP server is not yet available on Codex, the `slack-search` skill cannot query your workspace there.

### Installing the skills for another agent

The skills can be installed on their own into any of the 77 agents supported by the [`skills` CLI](https://github.com/vercel-labs/skills#supported-agents):

```sh
npx skills add slackapi/slack-skills-plugin -a <agent>
```

Name the agent with its own identifier. A few of the popular ones, along with where each installs the skills in your project:

| Agent | Identifier | Skills directory |
|-------|------------|------------------|
| Crush | `crush` | `.crush/skills/` |
| Devin for Terminal | `devin` | `.devin/skills/` |
| Gemini CLI | `gemini-cli` | `.agents/skills/` |
| Hermes Agent | `hermes-agent` | `.hermes/skills/` |
| OpenClaw | `openclaw` | `skills/` |
| OpenCode | `opencode` | `.agents/skills/` |
| Pi | `pi` | `.pi/skills/` |

Repeat `-a` to reach several agents at once, or use `-a '*'` for every agent detected in your project. Add `--list` to see the available skills without installing them.

This installs the skills only. There is no MCP server on this path, so the `slack-search` skill cannot query your workspace.

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
| `test-slack-app` | Run an existing Slack app in a [developer sandbox](/tools/developer-sandboxes) and get guided, source-specific steps to confirm it works in Slack. | _"Help me check that my Slack app actually works."_ |