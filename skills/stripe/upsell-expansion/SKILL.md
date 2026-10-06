---
name: upsell-expansion
description: "Finds expansion revenue opportunities in Stripe -- add-ons, seat upgrades, plan upgrades, and net revenue retention (NRR). Use when the user mentions \"expansion revenue\", \"upsell\", \"NRR\", \"net revenue retention\", \"add-ons\", or \"grow existing accounts\". For downgrades/proration, see subscription-plan-changes."
metadata:
  version: 1.0.0
---

> Adapted by Vitor Dvorschi (Appyon) from [appeeky/stripe-skills](https://github.com/appeeky/stripe-skills) (MIT License, (c) 2026 Erencan).

# Upsell & Expansion

## Stripe MCP Setup

Requires **Stripe MCP** (https://docs.stripe.com/mcp). `GetMcpTools` before `CallMcpTool`. Paginate all lists (`limit: 100`, `starting_after` while `has_more`). Amounts in **cents**. Read-only for audits; confirm before writes.

## Workflow

1. List active subs with items expanded
2. Segment:
   - Single-plan subs -> upsell to higher tier / add-ons
   - Users near usage/seat limits (if metadata tracks it)
   - Long-tenure subs on legacy low prices
3. Compute **NRR** = (start MRR + expansion - contraction - churn) / start MRR

## Output Template

```
Expansion Opportunities

NRR (last period): [X]% (benchmark: >100% is expansion-positive)

| Segment | Subs | Current MRR | Upsell path | Est. uplift |
|---------|------|-------------|-------------|-------------|
| No add-on | | | Agent add-on | |
| Starter 12mo+ | | | -> Pro | |

Priority: [highest-uplift, lowest-friction segment]
```

Cross-check add-on attach rate against `pricing-products-audit`.
