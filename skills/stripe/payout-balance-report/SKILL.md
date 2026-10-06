---
name: payout-balance-report
description: "Reports Stripe balance, available/pending funds, payouts, and cash flow. Use when the user asks \"Stripe balance\", \"payouts\", \"how much money in Stripe\", or \"when do we get paid\"."
metadata:
  version: 1.0.0
---

> Adapted by Vitor Dvorschi (Appyon) from [appeeky/stripe-skills](https://github.com/appeeky/stripe-skills) (MIT License, (c) 2026 Erencan).

# Payout & Balance Report

## Stripe MCP Setup

Requires **Stripe MCP** connected via OAuth or restricted key. Docs: https://docs.stripe.com/mcp

1. `GetMcpTools` with `server: "user-Stripe"` (or `plugin-stripe-stripe`) before any call
2. Prefer `stripe_api_search` → `stripe_api_details` → `stripe_api_read` for list/retrieve
3. **Always paginate** — `limit: 100`, follow `has_more` with `starting_after`
4. Amounts are in **cents** unless noted
5. Never expose secret keys in output

## Workflow

1. `GetBalance` — available vs pending per currency
2. `GetPayouts` — recent `limit: 20`, status `paid` / `in_transit` / `failed`
3. `GetBalanceTransactions` — last 30d summary (charges, fees, refunds)

## Output Template

```
Balance Snapshot

Available: $[X]
Pending:   $[Y]

Recent payouts:
| Date | Amount | Status | Arrival |

Net last 30d (after fees): $[Z]
```
