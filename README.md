# AgentWeb Documentation

User guide and reference for the AgentWeb Customer Portal at [app.agentweb.pro](https://app.agentweb.pro).

Every push to `main` deploys to production automatically.

## What's in this repo

| Path | Contents |
|---|---|
| `index.mdx` | Welcome page (Onboarding group) |
| `playbooks/` | Setup and how-to guides (e.g. connecting Emma to Claude, Claude Code, Codex, OpenClaw) |
| `onboarding/` | First-run setup (brand onboarding, organization sharing) — *to be added* |
| `user-guide/` | Portal reference (Agent Mode, Brand Hub, Growth Hub, Creative Hub, Performance Hub, Tasks) — *to be added* |
| `docs.json` | Site configuration: navigation, brand, colors, fonts, contextual menu |
| `logo/`, `favicon.svg` | AgentWeb brand assets |
| `snippets/` | Reusable MDX fragments |
| `images/` | Screenshots and inline graphics |

## Local development

Install the `mint` CLI and preview against `docs.json`:

```bash
npm i -g mint
mint dev
```

The preview runs at `http://localhost:3000` and live-reloads as you edit MDX files.

Check for broken links before opening a PR:

```bash
mint broken-links
```

## Writing standards

Read [`AGENTS.md`](./AGENTS.md) before editing pages. It defines the voice, terminology, and what to avoid. The short version: plain, instructional, no marketing copy, no editorializing. Stripe docs are the reference.

See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for the PR workflow.

## Deployment

Changes pushed to `main` deploy to production automatically. Preview branches deploy to per-branch URLs so you can review before merging.

## Need help?

Email [support@agentweb.pro](mailto:support@agentweb.pro).
