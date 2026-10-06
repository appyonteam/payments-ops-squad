---
name: customer-segmentation
description: "Segments the Stripe subscriber base by plan, country, card funding, tenure, or value -- with per-segment MRR and churn. Use when the user mentions \"segment customers\", \"break down by country/plan\", \"who are our best customers\", or \"value tiers\". For a single customer, see customer-360."
metadata:
  version: 1.0.0
---

> Adapted by Vitor Dvorschi (Appyon) from [appeeky/stripe-skills](https://github.com/appeeky/stripe-skills) (MIT License, (c) 2026 Erencan).

# Customer Segmentation

## Stripe MCP Setup

Requires **Stripe MCP** (https://docs.stripe.com/mcp). `GetMcpTools` before `CallMcpTool`. Paginate all lists (`limit: 100`, `starting_after` while `has_more`). Amounts in **cents**. Read-only for audits; confirm before writes.

## Workflow

1. List active + past_due subs (expand price + payment method)
2. Segment along a chosen axis:

| Axis | Source |
|------|--------|
| Plan | `price.id` |
| Country | `card.country` / customer address |
| Funding | `card.funding` |
| Tenure | `created` bucketed |
| Value | MRR tiers (whale / mid / low) |

3. Per segment: count, MRR, share, past_due rate

## Output Template

```
Segmentation by [axis]

| Segment | Subs | MRR | % of MRR | Past due % |
|---------|------|-----|----------|------------|

Concentration: top [n] customers = [X]% of MRR
Insight: [risk or opportunity per segment]
```

High MRR concentration = revenue risk; flag if top 10% > 50% of MRR.
