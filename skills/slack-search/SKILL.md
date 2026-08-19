---
name: slack-search
description: "Use when locating messages, files, channels, or people across Slack, or gathering context before answering, with the search MCP tools (slack_search_public, slack_search_public_and_private, slack_search_channels, slack_search_users). Covers search modifiers (in:, from:, before:), file-type filters, natural-language vs. keyword search, and reading results in context."
---

# Slack Search

This skill provides guidance for effectively searching Slack to find messages, files, and information.

## When to Use

Apply this skill whenever you need to find information in Slack, including when a user asks you to locate messages, conversations, files, or people, or when you need to gather context before answering a question about what's happening in Slack.

## Search Tools Overview

| Tool                              | Use When                                                                             |
| --------------------------------- | ------------------------------------------------------------------------------------ |
| `slack_search_public`             | Searching public channels only. Does not require user consent.                       |
| `slack_search_public_and_private` | Searching all channels including private, DMs, and group DMs. Requires user consent. |
| `slack_search_channels`           | Finding channels by name or description.                                             |
| `slack_search_users`              | Finding people by name, email, or role.                                              |

## Search Strategy

### Start Broad, Then Narrow

1. Begin with a simple keyword or natural language question.
2. If too many results, add filters (`in:`, `from:`, date ranges).
3. If too few results, remove filters and try synonyms or related terms.

### Choose the Right Search Mode

- **Natural language questions** (e.g., "What is the deadline for project X?"): Best for fuzzy, conceptual searches where you don't know exact keywords.
- **Keyword search** (e.g., `project X deadline`): Best for finding specific, exact content.

### Use Multiple Searches

Don't rely on a single search. Break complex questions into smaller searches:

- Search for the topic first
- Then search for specific people's contributions
- Then search in specific channels

## Search Modifiers Reference

### Location Filters

- `in:channel-name`: Search within a specific channel
- `in:<#C123456>`: Search in channel by ID
- `-in:channel-name`: Exclude a channel
- `in:<@U123456>` or `in:@username`: Search in DMs with a user

### User Filters

- `from:<@U123456>`: Messages from a specific user (by ID)
- `from:username`: Messages from a user (by Slack username)
- `to:<@U123456>`: Messages sent to a specific user
- `to:me`: Messages sent directly to you
- `creator:@username`: Canvases created by a specific person

### Content Filters

- `is:thread`: Only threaded messages
- `is:saved`: Only your saved messages
- `has:pin`: Pinned messages
- `has:link`: Messages containing links
- `has:file`: Messages with file attachments
- `has::emoji:`: Messages with a specific reaction
- `hasmy::emoji:`: Messages you reacted to with a specific reaction

### Date Filters

- `before:YYYY-MM-DD`: Messages before a date
- `after:YYYY-MM-DD`: Messages after a date
- `on:YYYY-MM-DD`: Messages on a specific date
- `during:month`: Messages during a specific month (e.g., `during:january`)

### Text Matching

- `"exact phrase"`: Match an exact phrase
- `-word`: Exclude messages containing a word
- `wild*`: Wildcard matching (minimum 3 characters before `*`)

## File Search

To search for files, set the `content_types="files"` parameter and use a `type:` filter in the query:

- `type:images`, `type:documents`, `type:pdfs`, `type:spreadsheets`, `type:presentations`
- `type:canvases`, `type:lists`, `type:emails`, `type:audio`, `type:videos`

Example: `content_types="files" type:pdfs budget after:2025-01-01`

All the standard modifiers above (`in:`, `from:`, dates, etc.) work with file searches too.

## Useful Parameters

Beyond the query string, the search tools accept parameters that materially improve results:

- `sort`: `score` (relevance, default) or `timestamp` (newest first); pair with `sort_dir` (`asc`/`desc`).
- `content_types`: `messages` (default) or `files`.
- `only_my_channels`: restrict to channels you're a member of.
- `limit`: results per page (capped at 20); paginate with the returned `cursor`.

## Following Up on Results

After finding relevant messages:

- Use `slack_read_thread` to get the full thread context for any threaded message.
- Use `slack_read_channel` with `oldest`/`latest` timestamps to read surrounding messages for context.
- Use `slack_read_user_profile` to identify who a user is when their ID appears in results.
- Use `slack_read_file` to read the contents of a file surfaced by a file search.
- Use `slack_list_channel_members` to see who is in a channel you found.

## Common Pitfalls

- **Boolean operators don't work.** `AND`, `OR`, `NOT` are not supported. Use spaces (implicit AND) and `-` for exclusion. (Repeating the same modifier, e.g. two `from:`, ORs those values together.)
- **Parentheses don't work.** Don't try to group search terms with `()`.
- **Search is not real-time.** Very recent messages (last few seconds) may not appear in search results. Use `slack_read_channel` for the most recent messages.
- **Private channel access.** Use `slack_search_public_and_private` when you need to include private channels, but note this requires user consent.

## Notes

- **Scope:** this skill owns searching _workspace content_: messages, files, channels, and people inside Slack. To search and read the official Slack _platform documentation_ at docs.slack.dev (conceptual and how-to questions about Slack features), use the `slack:slack-docs` skill instead.
