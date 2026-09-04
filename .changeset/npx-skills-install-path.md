---
"slack": patch
---

Document installing the skills with `npx skills`, which reaches coding agents beyond the three with a plugin surface:

```bash
# Install the skills for a coding agent, named by its own identifier
npx skills add slackapi/slack-skills-plugin -y -a <agent>

# For example, Gemini CLI or OpenCode
npx skills add slackapi/slack-skills-plugin -y -a gemini-cli
npx skills add slackapi/slack-skills-plugin -y -a opencode
```

This path already worked and needed no changes here, it was just undocumented. It carries the skills only: no commands, and no MCP server.
