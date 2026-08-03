---
"slack": patch
---

Document that `slack_read_thread` takes the thread timestamp as `message_ts`, not `thread_ts`. Search permalinks surface this value as `?thread_ts=<ts>`, so the slack-search skill and the find-discussions, standup, and summarize-channel commands now call out the correct parameter name to prevent a failed first call and retry.
