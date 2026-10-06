---
name: revenue-recognition
description: "Explains and computes deferred revenue, recognized revenue, and MRR-vs-cash differences from Stripe data for accounting. Use when the user mentions \"revenue recognition\", \"deferred revenue\", \"recognized revenue\", \"accrual\", \"MRR vs cash\", or \"annual plan accounting\". For cash collected, see invoice-revenue-audit."
metadata:
  version: 1.0.0
---

> Adapted by Vitor Dvorschi (Appyon) from [appeeky/stripe-skills](https://github.com/appeeky/stripe-skills) (MIT License, (c) 2026 Erencan).

# Revenue Recognition

## Stripe MCP Setup

Requires **Stripe MCP** (https://docs.stripe.com/mcp). `GetMcpTools` before `CallMcpTool`. Paginate all lists (`limit: 100`, `starting_after` while `has_more`). Amounts in **cents**. Read-only for audits; confirm before writes.

## Concept

Cash is not recognized revenue. An annual plan bills $120 upfront (cash) but recognizes $10/month over 12 months (accrual). The unrecognized portion is **deferred revenue** (a liability).

## Workflow

1. List active subs with interval + amount
2. For annual/multi-month: compute recognized-to-date vs deferred remainder
3. Reconcile:

| Metric | Source |
|--------|--------|
| Cash collected | paid invoices (`invoice-revenue-audit`) |
| Recognized (period) | MRR * months elapsed |
| Deferred balance | prepaid - recognized |

## Output Template

```
Revenue Recognition ([period])

Cash collected: $[X]
Recognized revenue: $[Y]
Deferred revenue balance: $[Z]

Annual plans driving deferral: [n] subs, $[amount] deferred

Note: Stripe Revenue Recognition product automates this -- Dashboard -> Revenue.
```

For audited books, recommend Stripe's native Revenue Recognition (https://docs.stripe.com/revenue-recognition).
