---
name: slack-api
description: "Use when a developer asks which Slack Web API method does something, needs a method's OAuth scopes or token type, wants to call or test a family.method endpoint (chat.postMessage, conversations.history, users.info, views.open), is handling cursor pagination (next_cursor) or rate limits (tier/ratelimited/Retry-After), or is debugging errors like missing_scope, invalid_auth, or channel_not_found. Also trigger on a pasted slack.com/api/ URL or docs.slack.dev/reference/methods link."
argument-hint: "[method.name | family]"
---

# Slack Web API

Help the developer **discover** the right Web API method, **read its contract**, and **call** it correctly. Slack exposes hundreds of methods named in `family.method` dot notation (e.g. `chat.postMessage`, `conversations.history`) at `https://slack.com/api/<method>`. Every method's doc page follows a fixed URL pattern, so the contract for any method is always one fetch away.

If `$0` is provided, it is either a full `method.name` (jump to Step 2 to read its contract) or a `family` name (go to Step 1 and find it in the index).

> **Critical rules:**
>
> - Verify a method name and its required scopes against its doc page **before** calling it — never invent method names or guess scopes. Method names use `family.method` dot notation.
> - Every response has a top-level `ok` boolean. **Always check `ok`** before using the result; on `ok: false`, read the `error` string.
> - Method names, scopes, rate tiers, and arguments come from the **live doc page** (`https://docs.slack.dev/reference/methods/<method-lowercased>.md`). The docs are the source of truth — discover from the live index, read the contract from the method's own page.

> **DO NOT rules:**
>
> - DO NOT assume a method is GET — many are POST. Check the doc page.
> - DO NOT hardcode bearer tokens into committed code or share them in plain text.
> - DO NOT use deprecated methods (`files.upload`, `dialog.open`, `rtm.*`, `oauth.access`, `search.*`, `stars.*`, `reminders.*`) without checking the replacement — a deprecated method's own doc page names what supersedes it; prefer the replacement for new apps.
> - DO NOT paginate by incrementing a page number — Slack uses opaque cursors (see Step 5).

> **Execution posture — run reads, confirm writes:**
>
> - **Read-only methods** (`*.list`, `*.info`, `*.history`, `conversations.members`, `auth.test`, etc.) may be run directly to help the developer.
> - **State-changing or destructive methods** (`chat.postMessage`/`update`/`delete`, any `*.delete`/`*.remove`/`*.kick`/`*.archive`, and all `admin.*`) — prepare the exact command and **confirm with the developer before running it**.

---

## Fast Path (for clear, specific requests)

If the developer already knows the method — they named it, pasted a `https://slack.com/api/<method>` URL or a `docs.slack.dev/reference/methods/<method>` link, or gave a `family.method` — skip discovery:

1. Go to **Step 2** to read the method's contract.
2. Go to **Step 4** to call it (honoring the execution posture above).

**Full-workflow indicators** (start at Step 1):

- "Which method does X?" / "How do I list/fetch/post … via the API?"
- The capability is known but the method name is not.
- Exploratory questions about what the API can do.

---

## Step 1: Identify the Method (Discover)

Map the developer's intent to a family, then to a candidate method.

### Browsing the index

WebFetch the live method index:

```text
https://docs.slack.dev/reference/methods.md
```

It lists every Web API method in `family.method` notation with a one-line description and a link to that method's own doc page. It is complete and always current — scan it for a candidate, then follow the method's link into Step 2 to read the contract (the index has descriptions only; rate tier, scopes, token type, and pagination all live on the per-method page).

Never publish or call a method name you have not seen on a live page.

### Searching the docs

When you would rather search by keyword than scan the index, and the Slack CLI is available, use the `slack:slack-cli` skill — **Step 3: Searching Documentation (`slack docs search`)** — to query Slack's docs from the terminal. That step covers the command and flags; results will point you to the method's reference page, which you then read in Step 2. Without the CLI, WebFetch the index (`https://docs.slack.dev/reference/methods.md`) and scan it instead.

---

## Step 2: Read the Method Contract (Navigate)

Fetch the method's doc page with WebFetch. Either follow the method's link from the index (Step 1) or construct the URL — the path segment is **all-lowercase** and ends in `.md`:

```text
https://docs.slack.dev/reference/methods/<method-lowercased>.md
```

For example, `conversations.members` → `https://docs.slack.dev/reference/methods/conversations.members.md`, and `chat.postMessage` → `https://docs.slack.dev/reference/methods/chat.postmessage.md`. When in doubt about casing, follow the index link rather than building the URL by hand.

Every method page documents, consistently:

- **HTTP method** (GET / POST) and the endpoint `https://slack.com/api/<method>`
- **Required OAuth scopes** and the **token type** (bot `xoxb-` vs user `xoxp-`)
- **Arguments** — required vs optional, with types
- An **example request and response**
- An **errors table** (method-specific codes)
- The **rate-limit tier**

Extract the **required arguments** and **required scopes** before calling. For what these cross-cutting concepts _mean_ in general — beyond what the method page states — the canonical references are: the response envelope, POST bodies, and auth at `https://docs.slack.dev/apis/web-api.md`; pagination at `https://docs.slack.dev/apis/web-api/pagination.md`; and rate-limit tiers at `https://docs.slack.dev/apis/web-api/rate-limits.md`.

---

## Step 3: Authenticate and Scope

Calling any non-public method requires a token with the right scopes and type. This skill's job here is to determine, from the contract you read in Step 2, **which token type and scopes** the method needs — independent of how you ultimately send the token.

From the contract you read in Step 2:

- Confirm the **token type** — a bot token cannot call a user-only method (the method's doc page states which token types it accepts), and vice versa. For what each token prefix (`xoxb-`, `xoxp-`, `xapp-`) is and when to use it, see `https://docs.slack.dev/authentication/tokens.md`.
- Note the **required scopes**. If a call later fails with `missing_scope`, the response's `needed` and `provided` fields name the gap — add the `needed` scope to the app manifest and reinstall the app.
- `admin.*` methods require an Enterprise Grid **org-level** token.

A couple of methods need no auth: `api.test` (connectivity), `auth.test` (validates whatever token you do send) and `blocks.validate`.

You need a token only when the method requires one. There are two ways to get one — pick whichever fits the developer's setup. **The Slack CLI is optional**: if the developer does not have it and prefers not to install it, take Path B rather than forcing an install.

### Path A: Use the Slack CLI (if installed or wanted)

The CLI supplies an authenticated session, so once the developer is logged in you can call methods without handling a token yourself (Step 4, "Via the Slack CLI").

Use the `slack:slack-cli` skill — **Step 1: Detect the Slack CLI** — to check whether the public Slack CLI is installed and resolve its command name. That step also proposes installing the CLI when it is absent. The fingerprint check, alias fallback, and install instructions all live there; do not duplicate them here.

Once resolved, use the detected command name for **all** CLI commands in this skill. We refer to it as `SLACK_CMD` — substitute the actual resolved command name everywhere you see `SLACK_CMD`.

Use the `slack:slack-cli` skill — **Step 5: Authentication (`slack auth`)** — to check the developer's login state and, if needed, walk them through `slack login`. Authentication mechanics live there.

### Path B: No CLI — bring your own token

You do not need the CLI to call a method. Get a token of the type you determined above from the app's **OAuth & Permissions** page in the Slack app config (`https://api.slack.com/apps` → your app → **OAuth & Permissions** → **OAuth Tokens**): the **Bot User OAuth Token** (`xoxb-…`) or the **User OAuth Token** (`xoxp-…`). That page also lists the scopes currently granted — confirm the ones from Step 2 are present. Then send that token with curl or an SDK in Step 4 ("Via raw HTTP" / "Via an SDK").

---

## Step 4: Call the Method (Manage)

First apply the **execution posture**: if the method changes state (post/update/delete/archive/kick, or any `admin.*`), show the developer the exact command and get a yes before running it. Read-only calls can be run directly.

### Via the Slack CLI (if installed)

To call a method from the terminal, use the `slack:slack-cli` skill — **Step 4: Calling Web API Methods (`slack api`)**. That step covers the `SLACK_CMD api <method> key=value …` syntax so that it is not repeated here. Pass the required arguments you gathered from the method's doc page in Step 2.

The CLI uses the developer's authenticated session, so it is the simplest path once they are logged in (Step 3).

### Via raw HTTP (curl)

Use the **Bash tool** when the developer wants a raw request or isn't using the CLI. Send the token in the `Authorization` header — the bot or user token from Step 3 (Path B, or the CLI session).

**Form-encoded** (the default for most methods):

```bash
curl -s -X POST 'https://slack.com/api/conversations.list' \
  -H 'Authorization: Bearer xoxb-YOUR-TOKEN' \
  -d 'types=public_channel&limit=200'
```

**JSON body** (for methods taking complex arguments like `blocks`, `view`, `attachments`, `metadata`):

```bash
curl -s -X POST 'https://slack.com/api/chat.postMessage' \
  -H 'Authorization: Bearer xoxb-YOUR-TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{"channel":"C0123456789","text":"Hello from the API"}'
```

Check the method's page for which content type it expects. With form encoding, a structured argument is passed as a JSON-encoded string value (e.g. `blocks=[...]`).

### Via an SDK

In Bolt and the Slack SDKs, each method is a client function whose arguments match the doc page's argument table:

- **JavaScript:** `await client.chat.postMessage({ channel, text, blocks })`
- **Python:** `client.chat_postMessage(channel=channel, text=text, blocks=blocks)`

(Note the JS dot form `chat.postMessage` vs the Python underscore form `chat_postMessage`.) To construct the `blocks`/`view` payload these calls take, use the `slack:block-kit` skill — this skill treats that payload as an opaque argument and focuses on the method call around it.

---

## Step 5: Handle Pagination

Methods that return collections use **cursor pagination**, not page numbers. A method's doc page states whether it paginates, and the full list of cursor-paginated methods is under _Methods supporting cursor-based pagination_ at `https://docs.slack.dev/apis/web-api/pagination.md`:

1. Call with a `limit` (page size — check the method's max).
2. Read `response_metadata.next_cursor` from the response.
3. If it is **non-empty**, call again with `cursor=<next_cursor>`.
4. Repeat until `next_cursor` comes back empty.

```bash
# First page
curl -s -X POST 'https://slack.com/api/conversations.history' \
  -H 'Authorization: Bearer xoxb-YOUR-TOKEN' \
  -d 'channel=C0123456789&limit=200'

# Next page — pass the cursor from response_metadata.next_cursor
curl -s -X POST 'https://slack.com/api/conversations.history' \
  -H 'Authorization: Bearer xoxb-YOUR-TOKEN' \
  -d 'channel=C0123456789&limit=200&cursor=dXNlcjpVMDYxTkZUVDI='
```

Cursors are opaque — never construct, parse, or reuse an old one.

---

## Step 6: Handle Rate Limits and Errors

When `ok` is `false`, branch on the `error` string:

- For method-specific codes, read the **errors table** on the method's doc page (Step 2) — it lists every error that method returns, including cross-cutting ones like `not_authed`, `invalid_auth`, `missing_scope`, `channel_not_found`, and `invalid_arguments`.
- For what the envelope itself means (`ok`, `error`, `warning`, `response_metadata`), see _Evaluating responses_ at `https://docs.slack.dev/apis/web-api.md`.
- `response_metadata.messages` often pinpoints a malformed argument.

**Rate limits:** on HTTP `429` / `error: "ratelimited"`, honor the `Retry-After` response header (seconds) — wait, then retry. Do not retry in a tight loop. Each method's tier (1–4 or special) caps calls per minute; the tier table is at `https://docs.slack.dev/apis/web-api/rate-limits.md`, and newer non-Marketplace apps face stricter caps on some methods, so trust the method's own page for the exact number.

---

## Notes

- **Slack Lists** methods use the `slackLists.*` prefix — a bare `lists.*` name does not exist.
- **Scope:** this skill owns the method layer — which method, its contract, and the call around it. CLI auth and calls are delegated to `slack:slack-cli`; Block Kit payloads to `slack:block-kit`.
