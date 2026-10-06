# Changelog

All notable changes to this project are documented here. Versions follow semantic versioning.

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
