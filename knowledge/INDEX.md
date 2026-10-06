# Knowledge: documentation on demand with a local cache

This repository does not contain vendor documentation. Agents and skills read the official Stripe, Primer and FunnelFox
documentation on demand and keep a local copy in a cache, so the same page is not downloaded again for every question.

## Where the cache lives

The first match wins:

1. `$PAYMENTS_OPS_KNOWLEDGE`, if set.
2. `${CLAUDE_PLUGIN_DATA}/knowledge/`, when the plugin data directory is available.
3. `<dest>/payments-ops-squad/knowledge/` next to a script install (`install/install.sh` marks that folder as a cache).
4. `~/.claude/payments-ops-squad/knowledge/`.

The cache is plain Markdown, one file per page, grouped by host. Each file starts with a YAML header:

```yaml
---
source_url: https://docs.stripe.com/declines/codes.md
requested_url: https://docs.stripe.com/declines/codes
fetched_at: YYYY-MM-DDTHH:MM:SSZ
---
```

## How agents look things up

1. Search the cache first: `grep -ril "<term>" <cache>`. Read the matching file and check `fetched_at`.
2. If nothing matches, or the copy is older than the TTL, fetch the page with the `pay-docs` command or directly:
   `python3 tools/fetch_doc.py <url>`. To discover pages, fetch the vendor index first:
   `python3 tools/fetch_doc.py --index stripe|primer|funnelfox` (each vendor publishes an `llms.txt` with its page list).
3. If the cache is empty and the tool cannot run (for example in Claude web or app), go straight to the official documentation
   online and say so in Sources.
4. Cite the page as `source_url` plus `fetched_at`. Summarize in your own words; never paste vendor text into answers.

## What `tools/fetch_doc.py` does

- Accepts only these prefixes: `https://docs.stripe.com/`, `https://primer.io/docs/`, `https://funnelfox.com/docs/`.
  Any other URL is refused with exit code 2.
- Tries the Markdown form of the page first (`<url>.md`, or `index.md` for a folder URL), then the URL itself.
- Respects `robots.txt` (exit code 3 when disallowed) and identifies itself with the User-Agent
  `payments-ops-squad (+https://github.com/appyonteam/payments-ops-squad)`.
- Keeps each page for 14 days by default (`--max-age-days N`); `--refresh` downloads it again.
- Prints the cache file path on the first line, then the cached content.
- Python standard library only; writes nothing outside the cache directory.

## Sources

`knowledge/sources.json` lists the official documentation indexes and, for reference only, the public vendor repositories with
their licenses. The repositories are not downloaded automatically. See `THIRD_PARTY_NOTICES.md`.
