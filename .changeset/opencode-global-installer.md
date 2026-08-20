---
"slack": minor
---

Add a global OpenCode installer (`make opencode-install`) that copies the seven
canonical Slack skills, five namespaced `slack-*` commands, and the Slack MCP
config into `~/.config/opencode/`, plus a matching `make opencode-uninstall`
that removes only what the installer owns and a `make opencode-sync` that
re-copies owned content to catch drift from the canonical sources.
