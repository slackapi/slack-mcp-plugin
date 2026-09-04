# slack

## 1.4.0

### Minor Changes

- f2a4f53: Add the `slack` Codex marketplace, giving developers a production install path for the Slack plugin in Codex:
  
  ```sh
  codex plugin marketplace add slackapi/slack-skills-plugin
  codex plugin add slack@slack
  ```
  
  Until now the only marketplace this repo published was named `slack-dev`, so installing the plugin meant adding a marketplace labelled "dev" and running `codex plugin add slack@slack-dev`.
  
  If you installed under the old name, remove it before re-adding: Codex treats the two marketplaces as unrelated and will leave both installed and enabled.
  
  ```sh
  codex plugin remove slack@slack-dev
  codex plugin marketplace remove slack-dev
  ```

### Patch Changes

- 1579a07: Improve the docs.slack.dev page with clearer formatting. Document the `slack-docs` skill, which finds and reads official Slack dev docs as clean markdown to answer questions about the Slack platform.
- f1deaff: Document installing the skills with `npx skills`, which reaches coding agents beyond the three with a plugin surface:
  
  ```bash
  # Install the skills for a coding agent, named by its own identifier
  npx skills add slackapi/slack-skills-plugin -y -a <agent>
  
  # For example, Gemini CLI or OpenCode
  npx skills add slackapi/slack-skills-plugin -y -a gemini-cli
  npx skills add slackapi/slack-skills-plugin -y -a opencode
  ```
  
  This path already worked and needed no changes here, it was just undocumented. It carries the skills only: no commands, and no MCP server.

## 1.3.0

### Minor Changes

- c961f03: Add the test-slack-app skill: guide developers through running an app in a developer sandbox and verifying it responds in Slack.

### Patch Changes

- 77a1079: Clarify Claude and Cursor plugin manifest descriptions so both user and developer audiences are discoverable. The Codex manifest describes skills only and does not claim workspace interaction, since the MCP server is not wired into the Codex surface.
- c17458c: Sharpen the slack-messaging and slack-search skill guidance: clearer trigger descriptions, accurate standard-markdown formatting rules (tables, headers, code blocks), more search modifiers and parameters, and scope notes linking to related skills.
- 1251c73: Standardize every skill `description` to lead with its triggering conditions in consistent, impersonal phrasing, so the right skill loads more reliably for a given task. Documents the description convention in the maintainers guide and adds unit checks (length cap, trigger cue, impersonal voice) to keep future skills aligned.

## 1.2.0

### Minor Changes

- 937e74b: Add a Codex plugin surface. A new `.codex-plugin/plugin.json` manifest exposes the Slack skills to [Codex][codex], and a repo-scoped `.agents/plugins/marketplace.json` lets you install the plugin into Codex from a local checkout. The hosted MCP server is not yet wired into the Codex surface; skills only for now.

  [codex]: https://developers.openai.com/codex

- 5a6f612: Route general Slack documentation questions to the slack-docs skill. The slack-cli skill's docs search is now scoped to terminal-based lookups via `slack docs search`, removing the overlap with slack-docs.

### Patch Changes

- c4caf79: Add rumdl Markdown linting to `make lint`/`make format` and clean up formatting across the skill and command docs.
- f716403: Align the install-surface metadata across the Claude Code and Cursor plugin manifests. Refresh the `.claude-plugin/plugin.json` description, add a `repository` field to both manifests, point `homepage` at the `docs.slack.dev` developer hub, and add the JSON Schema reference to the Claude Code manifest for editor validation.
- 3906698: Automate release announcements to the internal maintainers' Slack channel from the release workflow.
- a3295d4: Teach the `block-kit` skill to preview blocks with the new `slack blocks preview` CLI command, which opens the Block Kit Builder with the blocks pre-loaded. The skill discovers the command's usage via `--help` rather than hard-coding flags, and falls back to the manual Block Kit Builder link when the CLI isn't installed. Also removes the redundant validation Escape Hatch, whose visual-debugging fallback is now covered by the richer preview step.
- 7bd09ea: Drop the `--experiment=sandboxes` flag from `slack sandbox` invocations in the `create-slack-app` skill. The experiment has been removed from `slack-cli`, so the flag now surfaces an unknown-experiment warning that can confuse users and agents.
- 9ea300a: Fix the `homepage` field in `.claude-plugin/plugin.json` to point to this repository instead of `slackapi/slack-mcp-cursor-plugin`, which does not exist and returned a 404.
- 9635a2f: Publish GitHub Releases from the release workflow so each tag has release notes.
- 46f5c53: Update the `homepage` field in `.claude-plugin/plugin.json` and repo links in docs to point to `slackapi/slack-skills-plugin`, the repository's new name.
