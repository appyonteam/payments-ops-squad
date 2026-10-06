---
name: dispute-refund-audit
description: "Reviews Stripe disputes, chargebacks, and refunds — volume, reasons, and revenue leakage. Use when the user mentions \"disputes\", \"chargebacks\", \"refunds\", or \"fraud losses\"."
metadata:
  version: 1.0.0
---

> Adapted by Vitor Dvorschi (Appyon) from [appeeky/stripe-skills](https://github.com/appeeky/stripe-skills) (MIT License, (c) 2026 Erencan).

# Dispute & Refund Audit

## Stripe MCP Setup

Requires **Stripe MCP** connected via OAuth or restricted key. Docs: https://docs.stripe.com/mcp

1. `GetMcpTools` with `server: "user-Stripe"` (or `plugin-stripe-stripe`) before any call
2. Prefer `stripe_api_search` → `stripe_api_details` → `stripe_api_read` for list/retrieve
3. **Always paginate** — `limit: 100`, follow `has_more` with `starting_after`
4. Amounts are in **cents** unless noted
5. Never expose secret keys in output

## Workflow

1. `GetDisputes` — recent, paginate
2. `GetRefunds` or failed/succeeded charges with `refunded: true`
3. Group by reason, amount, status (`needs_response`, `lost`, `won`)

## Benchmarks

Dispute rate < 0.75% of charges (card network threshold).

## Output Template

```
Disputes & Refunds ([period])

Disputes: [n] | $[amount] | Win rate: [%]
Refunds: [n] | $[amount]

Action items:
1. Respond to [n] needs_response before [date]
```
