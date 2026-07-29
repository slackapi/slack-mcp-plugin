---
"slack": minor
---

Add a Codex plugin surface. A new `.codex-plugin/plugin.json` manifest exposes the Slack skills to [Codex][codex], and a repo-scoped `.agents/plugins/marketplace.json` lets you install the plugin into Codex from a local checkout. The hosted MCP server is not yet wired into the Codex surface; skills only for now.

[codex]: https://developers.openai.com/codex
