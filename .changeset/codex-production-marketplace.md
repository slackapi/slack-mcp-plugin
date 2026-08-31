---
"slack": minor
---

Add the `slack` Codex marketplace, giving developers a production install path for the Slack plugin in Codex:

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
