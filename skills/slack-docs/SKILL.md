---
name: slack-docs
description: "Use when answering a conceptual or how-to question about Slack platform features, or when asked to look up, fetch, or summarize a docs.slack.dev page, including a pasted docs.slack.dev link. Covers finding and reading official Slack docs as clean markdown."
argument-hint: "[topic or docs.slack.dev URL]"
---

# Slack Platform Documentation

Help the developer **find** the right page on the official Slack documentation site (`https://docs.slack.dev`) and **read** it as clean markdown, so answers come from the live docs rather than memory. The site exposes three machine-readable surfaces an agent can use directly, with no authentication and no Slack workspace:

- A **search API method**: `GET https://docs.slack.dev/api/v1/search?query=<q>&category=<c>` returns ranked page hits as JSON. Scope every search with a `category` (guides, reference, a specific SDK, etc.); an uncategorized search skews heavily toward SDK pages.
- **Per-page markdown**: every page is available at its URL **+ `.md`** (e.g. `/quickstart.md`).
- **Index files**: `/llms.txt` (a curated overview) and `/llms-sitemap.md` (a list of every markdown page).

If `$0` is provided, it is either a `docs.slack.dev` URL (jump to the **Fast Path**) or a topic to search (start at **Step 1**). For a broad "how do I build X on Slack?" question rather than one specific page, read `https://docs.slack.dev/llms.txt` first; it is a curated, LLM-oriented overview of the platform and the recommended build path.

> **Critical rules:**
>
> - The docs are the **source of truth**. Do not answer a factual question about the Slack platform from memory; discover the page, fetch it, then answer from what it says.
> - Prefer the **`.md` version** of any page over the HTML version. It is cleaner for reading and quoting.
> - Every fetched markdown page begins with a `Source: <url>` line. Keep that URL so you can cite the page back to the developer.

> **DO NOT rules:**
>
> - DO NOT invent documentation URLs. Get them from the search API, the sitemap, or a link the developer gave you then verify by fetching.
> - DO NOT paraphrase a page you have not actually fetched. If a fetch fails, say so rather than filling the gap from memory.
> - DO NOT assume every URL has a `.md` version. If a fetch returns an error, fall back to the search API or the sitemap (Step 1) rather than guessing another URL.

---

## Fast Path (the developer already has a URL)

If the developer pasted a `https://docs.slack.dev/...` link, skip discovery and go straight to **Step 2** to fetch and read it.

---

## Step 1: Discover the Page (search)

Use the docs **search API** to find candidate pages. WebFetch this URL, with the query URL-encoded and a `category` to scope the results:

```text
https://docs.slack.dev/api/v1/search?query=<url-encoded query>&category=<category>&limit=5
```

**Always start with a `category`.** An uncategorized search is dominated by SDK reference pages (a query like `socket mode` or `oauth` can return a top 10 that is entirely Bolt/Node pages), which buries the conceptual and reference content most questions are actually about. Pick the starting category from the developer's intent:

- **`guides`** — the default for "how do I…", "what is…", and conceptual platform questions (Events API, OAuth, Socket Mode, manifests, modals, App Home). Start here when in doubt.
- **`reference`** — for a specific method, event, scope, object, or Block Kit element, especially an exact name like `chat.postMessage`.
- **A tool/SDK category** (`python`, `javascript`, `java`, `slack_cli`, `slack_github_action`, `deno_slack_sdk`) — only once you know the developer's tool. See **Step 3**.

So `socket mode` as a concept → `https://docs.slack.dev/api/v1/search?query=socket%20mode&category=guides&limit=5`.

The response is JSON:

```json
{
  "total_results": 12,
  "results": [
    { "url": "/apis/events-api/using-socket-mode", "title": "Using Socket Mode" }
  ],
  "limit": 5
}
```

Scan `results` for the best `title`/`url` match, then read it in **Step 2**. A query is **required**; calling the endpoint with no `query` returns a `400` with an `error` field.

Full set of categories:

| Category | Scopes results to |
|----------|-------------------|
| `guides` | Conceptual and how-to guides |
| `reference` | API reference: methods, events, scopes, objects, Block Kit |
| `changelog` | Changelog and release notes |
| `python` | Python tools (Bolt for Python, Python Slack SDK) |
| `javascript` | JavaScript tools (Bolt for JS, Node Slack SDK) |
| `java` | Java tools (Bolt for Java, Java Slack SDK) |
| `slack_cli` | Slack CLI docs |
| `slack_github_action` | Slack Send GitHub Action docs |
| `deno_slack_sdk` | Deno Slack SDK docs |

If a categorized search returns no good hit, widen it: try the other likely category (`guides` ⇄ `reference`), then drop `category` entirely as a last resort. An unrecognized value returns a `400` with an `error` field listing the valid categories, so re-run with one of those or with no category.

**Fallbacks** when search does not surface a good hit, or returns a `500`/temporary error (the endpoint is rate-limited and cached ~5 minutes):

- WebFetch `https://docs.slack.dev/llms-sitemap.md`, a flat list of every documentation page's `.md` URL, and scan it for the relevant path.
- For API reference lookups, the enriched index pages are often faster: `https://docs.slack.dev/reference/methods.md`, `.../events.md`, `.../scopes.md`, `.../objects.md`, and `.../block-kit.md` each list every item with a one-line description and a `.md` link.
- If the developer has the Slack CLI, `slack docs search "<query>"` does the same discovery from the terminal (see the `slack:slack-cli` skill).

---

## Step 2: Read the Page (fetch markdown)

Given a page reference (a `url` from Step 1, or a link the developer pasted), read its markdown:

1. Normalize the reference to its `.md` URL:
   - A site-relative path from Step 1 (e.g. `/apis/events-api/using-socket-mode`): prepend `https://docs.slack.dev`.
   - A full URL the developer pasted: drop any `#anchor` first.
   - Append `.md`, e.g. `…/using-socket-mode` → `https://docs.slack.dev/apis/events-api/using-socket-mode.md`.
   The server lowercases `.md` requests, so casing does not matter: `chat.postMessage.md` and `chat.postmessage.md` both resolve.
2. **WebFetch** it. The page opens with `Source: <original-url>`; the rest is the page body in markdown.
3. Answer the developer from the fetched content, and cite the `Source` URL.

If a page is long and the developer asked something narrow, fetch it and quote only the relevant section rather than dumping the whole page.

---

## Step 3: Tool and SDK Documentation

Implementation details differ significantly between the official tools, so **establish which one the developer is using first**, then scope your reading to that tool's doc subtree. Each lives under `https://docs.slack.dev/tools/<name>` and its pages are fetchable as `.md` like any other (e.g. `https://docs.slack.dev/tools/bolt-js/concepts.md`). If the developer has not said, ask before assuming.

| Tool | Docs path | Search `category` | Use when the developer… |
|------|-----------|-------------------|--------------------------|
| **Slack CLI** | `/tools/slack-cli` | `slack_cli` | scaffolds, runs, or manages an app from the terminal; mentions `slack` commands or app manifests |
| **Bolt for JavaScript** | `/tools/bolt-js` | `javascript` | builds an app in Node/TypeScript with the Bolt framework |
| **Bolt for Python** | `/tools/bolt-python` | `python` | builds an app in Python with the Bolt framework |
| **Bolt for Java** | `/tools/java-slack-sdk` | `java` | builds an app in Java with Bolt (Bolt for Java lives in the Java SDK docs) |
| **Node Slack SDK** | `/tools/node-slack-sdk` | `javascript` | wants lower-level Node clients (`@slack/web-api`, `@slack/socket-mode`) without the full Bolt framework |
| **Python Slack SDK** | `/tools/python-slack-sdk` | `python` | wants the lower-level Python client without Bolt |
| **Java Slack SDK** | `/tools/java-slack-sdk` | `java` | wants Java clients, or is using Bolt for Java |
| **Slack Send GitHub Action** | `/tools/slack-github-action` | `slack_github_action` | sends data to Slack from a GitHub Actions workflow |

Once you know the tool, narrow discovery with the matching `category` from Step 1, e.g. `…?query=middleware&category=javascript`. Note the languages group: both Bolt for JavaScript and the Node Slack SDK fall under `javascript` (likewise `python` and `java` each cover their Bolt framework plus lower-level SDK), so the category scopes to the language family, not a single subtree.

**Bolt** is the framework built upon the matching language **SDK**. When unsure which subtree a topic lives in, fall back to the search API (Step 1) as it indexes all of these.
