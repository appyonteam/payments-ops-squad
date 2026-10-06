# payments-ops-squad

A team of payments operations specialists for Claude, covering **Stripe**, **Primer** and **FunnelFox**. It analyzes payment
exports, investigates incidents across the payment stack, explains decline codes from official sources and reviews routing,
retry and fraud rules. Every answer separates facts from hypotheses and cites the official source with a date.

## Who it is for

Payments, billing and revenue operations teams, product managers and engineers who run subscriptions or checkouts on a
FunnelFox, Primer and Stripe stack (or any part of it) and need evidence-based answers instead of guesses.

## Use cases

**Analyze an export**

```text
/payments-ops-squad:pay-export payments-export.csv What was the approval rate last week by country, per customer and per attempt?
```

The `analyze-export` skill detects the origin of the file, deduplicates it, checks daily coverage before computing any rate and
reports the customer view first, with numerator and denominator for every rate.

**Investigate an incident**

```text
/payments-ops-squad:pay-incident Approval dropped after a 3DS change in a workflow. What happened?
```

The `investigate-incident` skill confirms the drop is real, builds the change timeline, isolates the failing layer (app,
FunnelFox, Primer, processor, 3DS, network, issuer) and ranks hypotheses with the check that would confirm each one.

**Explain a decline code**

```text
/payments-ops-squad:pay-decline do_not_honor Stripe, recurring renewal, second retry
```

The `explain-decline` skill identifies the code namespace, paraphrases the official meaning with the URL and date, and says what
the source states about retrying and about the message shown to the customer.

## Specialists

| Specialist | Covers |
|---|---|
| `primer-squad` | Coordinates the Primer specialists for cross-domain investigations |
| `primer-payments` | Primer payment lifecycle: client session, authorization, capture, refunds, status |
| `primer-workflows` | Primer Workflows: routing, conditions, fallback, retries |
| `primer-3ds` | 3DS and SCA in Primer: frictionless vs challenge, authentication vs authorization |
| `primer-performance` | Approval, decline and 3DS rates, segmentation and statistical discipline |
| `primer-tokenization` | PAN, network tokens, processor tokens, stored credentials, CIT/MIT |
| `primer-integrations` | Processor connections, capabilities and processor-specific errors |
| `funnelfox-billing` | Subscriptions, checkout, orders, refunds and the `@funnelfox/billing` SDK |
| `funnelfox-api` | Public API, Billing API, web SDK and webhooks |
| `funnelfox-payments` | Payment status, declines and errors; which layer owns a failure |
| `funnelfox-orchestration` | Processor routing, cascading and fallback; who owns each rule |
| `funnelfox-retries` | Retries and recovery; coordination of retries across layers |
| `funnelfox-3ds` | 3DS across FunnelFox, Primer, the processor and the issuer |
| `funnelfox-tokenization` | Credentials that actually reach the processor |
| `funnelfox-performance` | Approval and conversion measured at the right grain |
| `funnelfox-integrations` | Processors supported by FunnelFox and responsibility per layer |
| Stripe skills (35) | MRR, churn, dunning, failed payments, disputes, Radar, payouts, reconciliation and more (start with `stripe-router`) |

Skills for the use cases: `analyze-export`, `investigate-incident`, `explain-decline`, `review-workflow`, `ask-payments`,
`fetch-docs`, plus `primer-core` and `funnelfox-core` as entry points for each vendor.

## Installation

### Claude Code (plugin)

```bash
claude plugin marketplace add appyonteam/payments-ops-squad
claude plugin install payments-ops-squad@payments-ops-marketplace
```

Commands appear with the plugin namespace: `/payments-ops-squad:pay-export`, `/payments-ops-squad:pay-incident`,
`/payments-ops-squad:pay-decline`, `/payments-ops-squad:pay-workflow`, `/payments-ops-squad:pay-ask`,
`/payments-ops-squad:pay-docs`.

### Claude Code (install script, no namespace)

```bash
git clone https://github.com/appyonteam/payments-ops-squad.git
cd payments-ops-squad
bash install/install.sh            # user scope: ~/.claude
bash install/install.sh --scope project   # project scope: ./.claude
```

Commands are then `/pay-export`, `/pay-incident` and so on. Existing files are never overwritten without `--force`. On Windows
use `install/install.ps1` (`-Scope project`, `-Force`).

### Claude web and desktop app

Download the zips from the latest GitHub Release, then go to **Settings > Capabilities > Skills** and upload each zip you want.
Skills are available on the Pro, Max, Team and Enterprise plans and need code execution enabled. There are no subagents on web or
app: each specialist is uploaded as a skill and Claude applies its checklist directly.

Details: [docs/INSTALL.md](docs/INSTALL.md) (English) and [docs/INSTALL.pt-BR.md](docs/INSTALL.pt-BR.md) (Portuguese).
Commands and examples: [docs/USAGE.md](docs/USAGE.md).

## Documentation on demand

No vendor documentation is stored in this repository. When an answer needs it, `tools/fetch_doc.py` (or the `pay-docs` command)
fetches the official page from Stripe, Primer or FunnelFox, prefers its Markdown form, respects `robots.txt` and keeps a copy in a
local cache for 14 days. Answers cite the page as `source_url` plus `fetched_at`. Only official documentation prefixes are
accepted. See [knowledge/INDEX.md](knowledge/INDEX.md) and [knowledge/sources.json](knowledge/sources.json).

## Ground rules built into every specialist

- Read-only in production: changes are written as recommendations for a human to approve.
- Every claim cites its source and access date.
- Facts and hypotheses are kept apart; each hypothesis comes with the way to validate it.
- Customer or order conversion first, approval per attempt as a diagnostic; grains are never mixed in one ratio.
- No invented decline codes, network rules, benchmarks, targets or vendor behavior.
- Secrets are never printed.

## Limitations

- Agents are instructed to be read-only; this is not technically enforced (Bash). Use restricted read-only API keys.
- Three Stripe skills (`checkout-implementation`, `webhook-implementation`, `stripe-billing-context`) generate code or files.
- The `stripe-billing-context` skill writes stripe-billing-context.md with account details; keep it out of version control.
- Vendor behavior changes. Answers are only as current as the documentation fetched for them; check `fetched_at`.

## Trademarks

Independent project. Not affiliated with, endorsed by or sponsored by Stripe, Primer, FunnelFox or Adapty. Trademarks belong to
their owners.

## License and credits

MIT License, see [LICENSE](LICENSE). Created by Vitor Dvorschi (Appyon).

The Stripe skills are adapted from [appeeky/stripe-skills](https://github.com/appeeky/stripe-skills) (MIT License, (c) 2026
Erencan). See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
