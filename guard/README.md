# Documentation claim sweep

The pull-request guard checks newly added MDX lines for three kinds of factual drift:

- `/api/...` paths that are absent from registered backend routes
- bold UI labels in action instructions that are absent from Customer Portal source
- retired claims that must not reappear

`source-inventory.json` stores 128-bit SHA-256 prefixes rather than source strings. This lets the public documentation repository verify membership without publishing private backend routes or Customer Portal source copy. The file records the exact source revisions used to generate it.

Regenerate the inventory from clean checkouts at current `main`:

```bash
python3 scripts/build_source_inventory.py \
  --agentweb-root ../agentweb \
  --portal-root ../agentweb-customer-portal \
  --output guard/source-inventory.json
```

Do not hand-edit inventory hashes. Review a regeneration by checking both recorded revisions, the generator diff, and the focused tests.

The CI validator reads only lines added by the pull request. Existing documentation remains a fixed baseline, while any new claim must match the source inventory. A bold span is treated as a UI label only when its line contains an action verb such as “click,” “select,” or “open.” Breadcrumb labels separated by `→` are checked one segment at a time.

`retired-claims.sha256` stores a word count plus a digest. The validator hashes every same-length word window, so a retired sentence is caught even when embedded in a longer paragraph without exposing the false claim in this public repository.
