# Changelog

All notable changes to this project are documented here. Versions follow semantic versioning.

## [0.3.0] - 2026-10-16

### Added
- 8 Solidgate specialist agents: `solidgate-api-architect`, `solidgate-payment-performance`, `solidgate-routing`,
  `solidgate-3ds-risk`, `solidgate-billing`, `solidgate-chargebacks`, `solidgate-reconciliation` and
  `solidgate-incident-investigator`, with hand-offs to the Primer, FunnelFox and Stripe specialists.
- 4 skills: `solidgate-core` (entry point), `solidgate-payment-form`, `solidgate-h2h` and `solidgate-chargebacks-alerts`. All
  are original work written from the public documentation; no Solidgate skill package is redistributed.
- `knowledge/solidgate/`: 13 diagnosis playbooks (most marked draft), a cross-provider equivalence matrix and metadata indexes.
- `tools/sync_solidgate.py`: builds the local Solidgate base (guides from the sitemap, API reference, OpenAPI v1 and v2) in the
  user's cache, honoring `robots.txt` (`docs.solidgate.com` disallows `/api/`).
- `mcp/solidgate-readonly/`: optional read-only MCP server on mock fixtures, not validated against the live API.
- `tools/fetch_doc.py` accepts `https://docs.solidgate.com/` and `https://api-docs.solidgate.com/`; `--index solidgate`.
- Use-case skills and commands route Solidgate questions to `solidgate-core`.
- The install scripts also copy `tools/sync_solidgate.py`, `knowledge/solidgate/` (into the cache) and the MCP server.
- Tests: Solidgate agent pattern and hand-off targets, no vendor documentation in the repository, allowlist, sync and MCP.
- Totals: 29 agents, 47 skills (35 Stripe and 12 own), 6 commands, 76 zips.

### Unchanged
- The 21 agents published in 0.1.0 and 0.2.0.

## [0.2.0] - 2026-10-06

### Added
- 5 Stripe specialist agents: `stripe-payments`, `stripe-risk`, `stripe-disputes`, `stripe-billing` and `stripe-finance`. Each
  skill (34, all but `stripe-router`) belongs to exactly one agent, with explicit hand-offs and cross-references between agents.
- "Agent" column in the `stripe-router` routing table; the router stays the entry point. Recorded in THIRD_PARTY_NOTICES.
- "Stripe specialists" section in the README with the full table of Stripe skills grouped by agent.
- Tests: every Stripe skill is owned by exactly one agent (no orphan, no duplicate) and each `stripe-*` agent follows the pattern.
- Totals: 21 agents, 43 skills (35 Stripe and 8 own), 6 commands, 64 zips.

### Known gap
- No dedicated Early Fraud Warning skill yet. `stripe-disputes` covers the topic from stable concepts and the official
  Stripe documentation, and marks deadlines, program rules and refund effects as "confirm in docs.stripe.com".

## [0.1.0] - 2026-10-06

### Added
- 16 specialists as Claude Code agents: 7 for Primer (including the `primer-squad` coordinator) and 9 for FunnelFox.
- 35 Stripe skills adapted from appeeky/stripe-skills (MIT), with attribution.
- 8 skills: `primer-core`, `funnelfox-core`, `analyze-export`, `investigate-incident`, `explain-decline`, `review-workflow`,
  `ask-payments` and `fetch-docs`.
- 6 commands: `pay-export`, `pay-incident`, `pay-decline`, `pay-workflow`, `pay-ask` and `pay-docs`.
- Documentation on demand: `tools/fetch_doc.py` fetches official Stripe, Primer and FunnelFox pages into a local cache with
  source URL and fetch date (14-day TTL, robots.txt respected, official prefixes only). No vendor content in the repository.
- Claude Code plugin and marketplace manifests.
- Install scripts for user and project scope (`install/install.sh`, `install/install.ps1`).
- Build of one zip per skill for Claude web and app (`tools/build_dist.py`).
- Sanitization gate (`tools/gate.py`) and unit tests.
