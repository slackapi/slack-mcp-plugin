---
"slack": patch
---

Document installing the skills with the `skills` CLI, which reaches 77 agents beyond the three with a plugin surface (Gemini CLI, OpenCode, Zed, Warp, Amp, and more):

```sh
npx skills add slackapi/slack-skills-plugin -a <agent>
```

This path already worked and needed no changes here, it was just undocumented. It carries the skills only: no commands, and no MCP server.
