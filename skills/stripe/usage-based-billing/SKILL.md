---
name: usage-based-billing
description: "Designs and audits usage-based/metered Stripe billing -- meters, usage records, tiered pricing, and credit burn-down. Use when the user mentions \"usage-based billing\", \"metered billing\", \"pay per use\", \"meters\", \"credits\", \"consumption pricing\", or \"overage\". For flat recurring, see pricing-products-audit."
metadata:
  version: 1.0.0
---

> Adapted by Vitor Dvorschi (Appyon) from [appeeky/stripe-skills](https://github.com/appeeky/stripe-skills) (MIT License, (c) 2026 Erencan).

# Usage-Based Billing

## Stripe MCP Setup

Requires **Stripe MCP** (https://docs.stripe.com/mcp). `GetMcpTools` before `CallMcpTool`. Paginate all lists (`limit: 100`, `starting_after` while `has_more`). Amounts in **cents**. Read-only for audits; confirm before writes.

## Concepts

| Model | Setup |
|-------|-------|
| Pure metered | Meter + usage-based price; bill actual usage |
| Prepaid credits | Credit grant burns down with usage |
| Hybrid | Base subscription + overage above included quota |

Modern Stripe uses **Meters** + **Meter Events** (`billing/meter-events`), replacing legacy usage records.

## Workflow

1. Review prices: `GetPrices` -- look for metered usage_type / meter-linked
2. Check meter definitions (Dashboard -> Billing -> Meters)
3. Verify usage reporting path in code (meter events sent on each usage)

## Design Checklist

- [ ] Meter defined with aggregation (sum/count/last)
- [ ] Price linked to meter
- [ ] Usage events sent reliably (idempotent, retried)
- [ ] Included quota vs overage tiers defined
- [ ] Customer-facing usage visibility

## Output Template

```
Usage Billing Audit

Metered prices: [n]
Meters: [list + aggregation]
Usage reporting: [reliable / gaps]
Model: [pure metered / credits / hybrid]

Recommendation: [tiering / quota / reliability fix]
```

For complex credit/commit models, note Metronome + Stripe pattern (see Stripe docs).
