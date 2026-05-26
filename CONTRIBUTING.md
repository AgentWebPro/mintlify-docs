# Contributing

How to edit and ship changes to the AgentWeb documentation.

## Quick start

```bash
git clone git@github.com:AgentWebPro/mintlify-docs.git
cd mintlify-docs
npm i -g mint
mint dev
```

The preview runs at `http://localhost:3000` and live-reloads on save.

Requires Node.js 19 or higher.

## Editing workflow

1. Create a branch off `main`. Name it `docs/<short-description>` or use the auto-named `admin-mcp/...` branch if you are editing in the hosted web editor.
2. Make your changes. Read [`AGENTS.md`](./AGENTS.md) first if you have not. It defines the voice and terminology.
3. Run `mint broken-links` and fix anything that is flagged.
4. Open a PR against `main`. A preview URL is generated on every push.
5. Get a review. Merge.

Merges to `main` deploy to production automatically.

## Useful commands

| Command | What it does |
|---|---|
| `mint dev` | Local preview at `http://localhost:3000` |
| `mint dev --port 3333` | Run on a different port if 3000 is taken |
| `mint broken-links` | Scan for broken internal and external links |
| `mint update` | Update the CLI to the latest version |

If `mint dev` fails with a `sharp` module error, upgrade Node to 19+, then `npm remove -g mint && npm i -g mint`.

## Where to put new content

| Type of content | Location |
|---|---|
| First-run setup (brand, integrations, team) | `onboarding/` |
| Portal reference (Agent Mode, hubs, Tasks) | `user-guide/` |
| Setup guides for specific clients or workflows (e.g. Connect Emma) | `playbooks/` |
| Reusable MDX fragments | `snippets/` |
| Screenshots and inline graphics | `images/` |
| API reference (when added) | `api-reference/` |

Add new pages to the navigation in `docs.json` under the relevant tab and group. If a page isn't in `docs.json`, it won't show up in the sidebar.

## Site config

Top-level site settings (brand colors, font, navbar links, footer, contextual menu) live in `docs.json`. The `$schema` field at the top of `docs.json` points to the full schema reference.

Do not change navigation, theme, or brand colors without a heads-up. Those affect every page.

## Reviewing PRs

Check:

- Voice matches `AGENTS.md`. No marketing, no editorializing, no rule-of-three.
- New pages are added to `docs.json` navigation.
- Screenshots are committed under `images/`, not linked from external hosts.
- `mint broken-links` is clean.
- The preview URL renders correctly. Pay attention to `<Steps>`, `<Tabs>`, `<AccordionGroup>`, and code blocks.

## Reporting issues

Open an issue against this repo, or email [support@agentweb.pro](mailto:support@agentweb.pro) if the docs are blocking a customer.
