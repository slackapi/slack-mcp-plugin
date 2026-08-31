import { readFile } from "node:fs/promises";

const CANONICAL_COMMANDS = Object.freeze([
  ["slack-channel-digest", "channel-digest.md"],
  ["slack-draft-announcement", "draft-announcement.md"],
  ["slack-find-discussions", "find-discussions.md"],
  ["slack-standup", "standup.md"],
  ["slack-summarize-channel", "summarize-channel.md"],
]);

const SLACK_MCP = Object.freeze({
  type: "remote",
  url: "https://mcp.slack.com/mcp",
  oauth: Object.freeze({
    clientId: "{env:SLACK_OPENCODE_CLIENT_ID}",
    redirectUri: "http://127.0.0.1:19876/mcp/oauth/callback",
  }),
});

function parseCommand(source, name) {
  const match = source.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
  if (!match) {
    throw new Error(`Canonical command ${name} is missing YAML frontmatter`);
  }

  const description = match[1].match(/^description:\s*(.+)$/m)?.[1];
  if (!description) {
    throw new Error(`Canonical command ${name} is missing a description`);
  }

  return { description, template: match[2].trim() };
}

async function readCanonicalCommands() {
  const commands = await Promise.all(
    CANONICAL_COMMANDS.map(async ([name, filename]) => {
      const source = await readFile(new URL(`../../commands/${filename}`, import.meta.url), "utf8");
      return [name, parseCommand(source, name)];
    }),
  );
  return Object.fromEntries(commands);
}

export async function registerCommandsAndMcp(config) {
  const commands = await readCanonicalCommands();
  config.command ??= {};
  for (const [name, command] of Object.entries(commands)) {
    // User/project command definitions win over this plugin and make retries harmless.
    if (!Object.hasOwn(config.command, name)) config.command[name] = command;
  }

  config.mcp ??= {};
  // An explicitly configured Slack server is authoritative and is never replaced.
  if (!Object.hasOwn(config.mcp, "slack")) {
    config.mcp.slack = { ...SLACK_MCP, oauth: { ...SLACK_MCP.oauth } };
  }
}

export { CANONICAL_COMMANDS, SLACK_MCP };
