# Documentation project instructions

Instructions for humans and AI agents editing this docs site.

## About this project

- Documentation for the AgentWeb Customer Portal at [app.agentweb.pro](https://app.agentweb.pro).
- Pages are MDX files with YAML frontmatter. Site config lives in `docs.json`.
- Run `mint dev` to preview locally. Run `mint broken-links` before opening a PR.
- For component reference, frontmatter fields, and navigation tree syntax, refer to the `docs.json` schema (`$schema` field) and existing pages as examples.

## Voice

The reference is the [Stripe docs](https://docs.stripe.com). Read a few pages there before writing here.

**Do:**
- Write plain, instructional sentences. One idea per sentence.
- Address the reader as "you". Use active voice.
- Lead with what the reader is trying to do, not why it's great.
- Use sentence case for headings.
- Bold UI labels exactly as they appear: Click **Settings → API Keys**.
- Use code formatting for file names, commands, paths, URLs, and field names.
- Break up steps with numbered lists or the `<Steps>` component.
- Use tables for reference material (config options, scope grants, status codes).

**Don't:**
- Sell, persuade, or editorialize. Docs help the reader accomplish a task; they don't market the product.
- Anthropomorphize Emma beyond what's useful. "Emma drafts a post" is fine. "Emma is your AI partner" is marketing copy.
- Use rule-of-three flourishes ("X isn't Y. It's Z.") or rhetorical contrasts. They read as AI-generated.
- Use the em-dash habit (`—`) to chain clauses. A period works.
- Add "just", "simply", or "easily" to make something sound friendlier. Skip them.
- Add motivational closes ("you're ready to ship!", "the setup isn't the moat").
- Use marketing phrases: "powerful", "seamless", "world-class", "best-in-class", "supercharge", "unlock", "leverage".

## Terminology

| Use | Don't use |
|---|---|
| AgentWeb | Agent Web, agentweb |
| Customer Portal | the app, the platform |
| Emma | the agent, the AI, our agent |
| Knowledge Base | knowledgebase, KB |
| Agent Mode | chat, the chat interface |
| Brand Hub, Growth Hub, Creative Hub, Performance Hub | sections, hubs |
| Tasks | activities (in user-facing copy) |
| MCP | Model Context Protocol (spell out on first use per page) |
| API key | token, auth token (use "bearer token" only when describing the HTTP header) |

## Page structure

A typical reference page:

1. A one-sentence description of what the page covers (also goes in frontmatter `description`).
2. A short paragraph or table introducing the concept.
3. **Before you begin** — prerequisites, if any.
4. **Setup / How to / Steps** — numbered or `<Steps>`-wrapped procedural content.
5. **Reference tables** — fields, options, scopes.
6. **Troubleshooting** — `<AccordionGroup>` of common issues.
7. **Next steps** — 2–3 links to related pages. No motivational language.

## Agent-ready features

This site uses three features to make the docs useful for both humans and AI agents that consume them.

### Visibility

Use `<Visibility for="humans">` and `<Visibility for="agents">` to serve different content at the same URL. Humans get the rendered web page; agents fetching `page.md` get the agent-only blocks.

```mdx
<Visibility for="humans">
  Click **Settings → API Keys**, then **Generate**.
</Visibility>

<Visibility for="agents">
  POST /v1/api-keys with an empty body. Returns `{ "key": "aw_..." }`.
</Visibility>
```

### Prompt

Use `<Prompt>` to embed a ready-to-copy prompt readers can paste into Emma, Claude, Cursor, or any other AI tool.

```mdx
<Prompt description="Set up an AgentWeb workspace" icon="sparkles" actions={["copy", "cursor"]}>
  Walk me through setting up a new AgentWeb brand profile from scratch.
  Ask one question at a time and confirm my answers before saving.
</Prompt>
```

### Contextual menu

The floating toolbar on every page is configured in `docs.json` under `contextual.options`. Current options: `copy`, `view`, `chatgpt`, `claude`, `perplexity`, `mcp`, `cursor`, `vscode`. To change them, edit `docs.json`, not individual pages.

## Content boundaries

- Don't document internal admin or staff-only features. These docs are public.
- Don't include real customer names, account IDs, or live API keys in examples. Use placeholders (`aw_YOUR_API_KEY_HERE`).
- Don't link to internal Notion, Linear, or Slack URLs.
- Link to `start.agentweb.pro` for signup, `app.agentweb.pro` for the portal, `support@agentweb.pro` for help.

## When editing via the hosted web editor

The hosted editor saves to a branch (named `admin-mcp/...`) and pushes to GitHub when you click Save. Site config (`docs.json`) and page navigation are kept in sync. The editor and `git` can diverge — if you are editing both, pull the branch locally first and rebase the editor changes on top.
