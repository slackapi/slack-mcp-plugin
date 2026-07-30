---
"slack": patch
---

Teach the `block-kit` skill to preview blocks with the new `slack blocks preview` CLI command, which opens the Block Kit Builder with the blocks pre-loaded. The skill discovers the command's usage via `--help` rather than hard-coding flags, and falls back to the manual Block Kit Builder link when the CLI isn't installed. Also removes the redundant validation Escape Hatch, whose visual-debugging fallback is now covered by the richer preview step.
