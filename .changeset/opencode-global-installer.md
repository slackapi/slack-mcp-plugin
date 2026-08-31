---
"slack": minor
---

Replace the OpenCode installer, copied files, and symlink adapters with a native
git-backed plugin and config hook. OpenCode registers the seven canonical skills,
five `slack-*` commands, and OAuth-enabled Slack MCP configuration while
preserving an existing `mcp.slack` entry.
