---
name: financial-reconciliation
description: "Reconciles Stripe payouts to bank deposits and breaks down balance transactions -- gross, fees, refunds, net. Use when the user mentions \"reconciliation\", \"payout doesn't match bank\", \"Stripe fees\", \"balance transactions\", or \"where did the money go\". For balance snapshot only, see payout-balance-report."
metadata:
  version: 1.0.0
---

> Adapted by Vitor Dvorschi (Appyon) from [appeeky/stripe-skills](https://github.com/appeeky/stripe-skills) (MIT License, (c) 2026 Erencan).

# Financial Reconciliation

## Stripe MCP Setup

Requires **Stripe MCP** (https://docs.stripe.com/mcp). `GetMcpTools` before `CallMcpTool`. Paginate all lists (`limit: 100`, `starting_after` while `has_more`). Amounts in **cents**. Read-only for audits; confirm before writes.

## Workflow

1. `GetPayouts` -- target payout(s) with amount + arrival date
2. `GetBalanceTransactions` filtered by `payout` -- the transactions that composed it
3. Break down: gross charges - Stripe fees - refunds - adjustments = net payout

## Fee Analysis

Sum `fee` across balance transactions; compute effective % of gross.

## Output Template

```
Payout Reconciliation -- [payout_id]

Arrival: [date]  |  Net paid: $[X]

Composition:
| Type | Count | Gross | Fees | Net |
|------|-------|-------|------|-----|
| Charges | | | | |
| Refunds | | | | |
| Adjustments | | | | |

Effective Stripe fee: [X]% of gross
Bank match: [reconciled / discrepancy $Y]
```

Flag discrepancies between payout net and expected bank deposit.
