---
name: invoice-revenue-audit
description: "Reviews Stripe invoices — paid, open, uncollectible, revenue by period, and subscription billing health. Use when the user asks about \"invoices\", \"billing history\", \"uncollectible\", or \"collected revenue\" (cash, not MRR)."
metadata:
  version: 1.0.0
---

> Adapted by Vitor Dvorschi (Appyon) from [appeeky/stripe-skills](https://github.com/appeeky/stripe-skills) (MIT License, (c) 2026 Erencan).

# Invoice & Revenue Audit

## Stripe MCP Setup

Requires **Stripe MCP** connected via OAuth or restricted key. Docs: https://docs.stripe.com/mcp

1. `GetMcpTools` with `server: "user-Stripe"` (or `plugin-stripe-stripe`) before any call
2. Prefer `stripe_api_search` → `stripe_api_details` → `stripe_api_read` for list/retrieve
3. **Always paginate** — `limit: 100`, follow `has_more` with `starting_after`
4. Amounts are in **cents** unless noted
5. Never expose secret keys in output

## Workflow

1. `GetInvoices` — filter by `status`: `paid`, `open`, `uncollectible`, `void`
2. Sum `amount_paid` for paid invoices in period (cash collected)
3. Compare to MRR snapshot — gap explains one-time charges, prorations, credits

## Status Meanings

| Status | Action |
|--------|--------|
| `open` | Awaiting payment — check past_due subs |
| `paid` | Collected |
| `uncollectible` | Write-off — churn signal |
| `void` | Canceled invoice |

## Output Template

```
Invoice Summary ([period])

Paid: $[X] ([n] invoices)
Open: $[Y] ([n])
Uncollectible: $[Z]

vs MRR snapshot: [explain delta]
```
