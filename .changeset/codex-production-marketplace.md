---
"slack": minor
---

Add the `slack` Codex marketplace, giving developers a production install path for the Slack plugin in Codex:

```sh
codex plugin marketplace add slackapi/slack-skills-plugin
codex plugin add slack@slack
```

Codex resolves marketplace manifests from a fixed set of relative paths, so `.agents/plugins/marketplace.json` is the manifest developers get from this repo. It previously shipped as `slack-dev` with display name `Slack (dev)`, named for the plugin team's local testing rather than for the public install path it actually served, which made the install command read `slack@slack-dev`.

If you installed under the old name, remove it before re-adding: Codex treats the two marketplaces as unrelated and will leave both installed and enabled.

```sh
codex plugin remove slack@slack-dev
codex plugin marketplace remove slack-dev
```
