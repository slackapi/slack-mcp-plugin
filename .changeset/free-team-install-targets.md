---
"slack": minor
---

Offer a ranked set of install targets instead of treating a developer sandbox as the only option. `create-slack-app` Step 3 now presents a sandbox (recommended), a Free Team (second choice), or an existing production workspace (last resort, usually gated by admin app approval), and `test-slack-app` accepts a throwaway Free Team as a safe place to test. Also runs `sandbox list` and `sandbox create` non-interactively with `--team`, `--name`, and `--password`.
