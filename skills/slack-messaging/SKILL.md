---
name: slack-messaging
description: "Use when writing, drafting, scheduling, or improving a Slack message, announcement, or reply sent via the Slack MCP tools (slack_send_message, slack_send_message_draft, slack_schedule_message). Covers Slack markdown formatting, message structure, thread etiquette, reactions, and scheduling, and points to the right dialect for canvases and Block Kit."
---

# Slack Messaging Best Practices

This skill provides guidance for composing well-formatted, effective Slack messages.

## When to Use

Apply this skill whenever composing, drafting, or helping the user write a Slack message, including when using `slack_send_message`, `slack_send_message_draft`, or `slack_schedule_message`. The formatting rules below cover these message tools. `slack_create_canvas` uses a different, richer markdown dialect — see the Canvas note below.

## Formatting

The message tools (`slack_send_message`, `slack_send_message_draft`, `slack_schedule_message`) accept **standard markdown** and convert it to Slack formatting on send. Write normal markdown. Do **not** use Slack's legacy `mrkdwn` syntax (`*bold*`, `~strike~`); those single-character forms mean something different in standard markdown. Each text element is limited to ~5000 characters.

| Format        | Syntax                 |
| ------------- | ---------------------- |
| Bold          | `**text**`             |
| Italic        | `_text_` (or `*text*`) |
| Strikethrough | `~~text~~`             |
| Code (inline) | `` `code` ``           |
| Quote         | `> text`               |
| Link          | `[display text](url)`  |
| Bulleted list | `- item`               |
| Numbered list | `1. item`              |

Block elements also work. Write them as literal markdown:

- **Code block** with an optional language for syntax highlighting:

  ````text
  ```python
  print("hello")
  ```
  ````

- **Table** with `|` delimiters (escape a literal pipe inside a cell as `\|`):

  ```text
  | Feature | Status |
  |---------|--------|
  | Tables  | works  |
  ```

- **Headers** with `#` / `##` / `###`:

  ```text
  ## Section title
  ```

The one thing that does **not** embed in a message: inline images (`![alt](url)`) typically render as a plain link rather than an inline image. For rich embedded layouts (buttons, images, structured cards) you need Block Kit; for a document-style surface where images do embed, use a canvas. See the Notes below.

## Message Structure Guidelines

- **Lead with the point.** Put the most important information in the first line. Many people read Slack on mobile or in notifications where only the first line shows.
- **Keep it short.** Aim for 1-3 short paragraphs (the ~5000-character limit is a ceiling, not a target). If the message is long or structured, consider a Canvas instead.
- **Use line breaks generously.** Walls of text are hard to read. Separate distinct thoughts with blank lines.
- **Use bullet points for lists.** Anything with 3+ items should be a list, not a run-on sentence.
- **Bold key information.** Use `**bold**` for names, dates, deadlines, and action items so they stand out when scanning.

## Thread vs. Channel Etiquette

- **Reply in threads** when responding to a specific message to keep the main channel clean.
- **Use `reply_broadcast`** (also post to channel) only when the reply contains information everyone needs to see.
- **Post in the channel** (not a thread) when starting a new topic, making an announcement, or asking a question to the whole group.
- **Don't start a new thread** to continue an existing conversation; find and reply to the original message.

## Tone and Audience

- Match the tone to the channel: `#general` is usually more formal than `#random`.
- For simple acknowledgments, add an emoji reaction with `slack_add_reaction` instead of a reply message (use `slack_get_reactions` to read existing reactions).
- When writing announcements, use a clear structure: context, key info, call to action.

## Scheduling

- Use `slack_schedule_message` to post later. `post_at` is a Unix timestamp that must be at least 2 minutes in the future and at most 120 days out; the message body uses the same standard markdown as above.
- Scheduled messages can't be edited via the API once set — the user manages them from **Drafts & sent** in Slack.

## Notes

- **Canvas formatting is different.** `slack_create_canvas` uses Canvas-flavored Markdown, a richer dialect than the message tools: headers, tables, checklists, and inline images (`![alt](url)`) all embed, and it also supports user/channel reference cards, callouts, and columns. Do **not** assume the message rules above apply — follow the `slack_create_canvas` tool's own formatting guidance when composing a canvas.
- **Scope:** this skill owns composing and formatting the _text_ of messages sent through the Slack MCP message tools. For interactive layouts (buttons, menus, modals, Home tabs, or any Block Kit JSON), use the `slack:block-kit` skill, which composes and validates the block payload. For calling the Slack Web API directly (`chat.postMessage` and friends) rather than the MCP tools, use the `slack:slack-api` skill.
