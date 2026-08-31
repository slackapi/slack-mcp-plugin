---
"slack": patch
---

Rename the Codex marketplace in `.agents/plugins/marketplace.json` from `slack-dev` to `slack`, so the install command reads `codex plugin add slack@slack` instead of `slack@slack-dev`. The manifest was named for local testing, but Codex resolves marketplace manifests from a fixed set of relative paths, so this is also the manifest developers get when they run `codex plugin marketplace add slackapi/slack-skills-plugin`. Anyone who installed from the old name should run `codex plugin remove slack@slack-dev` and `codex plugin marketplace remove slack-dev` before re-adding.
