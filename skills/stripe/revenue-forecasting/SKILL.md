---
name: revenue-forecasting
description: "Projects future MRR, ARR, and revenue run-rate from current Stripe subscription trends, new-sub velocity, and churn. Use when the user asks \"revenue forecast\", \"MRR projection\", \"where will we be in 6 months\", \"ARR run-rate\", or \"growth trajectory\". For current MRR only, see mrr-arr-snapshot."
metadata:
  version: 1.0.0
---

> Adapted by Vitor Dvorschi (Appyon) from [appeeky/stripe-skills](https://github.com/appeeky/stripe-skills) (MIT License, (c) 2026 Erencan).

# Revenue Forecasting

## Stripe MCP Setup

Requires **Stripe MCP** (https://docs.stripe.com/mcp). `GetMcpTools` before `CallMcpTool`. Paginate all lists (`limit: 100`, `starting_after` while `has_more`). Amounts in **cents**. Read-only for audits; confirm before writes.

## Inputs to gather

1. Current MRR (via `mrr-arr-snapshot` logic)
2. New subs / month — count `active` subs created in last 30/60/90d (`created` filter)
3. Monthly churn % (via `churn-analysis`)
4. Avg new MRR per sub

## Model (simple)

```
Next month MRR = current_MRR * (1 - churn_rate) + new_MRR_added
```

Project 3/6/12 months. Show best / base / worst (churn +/-2pp, growth +/-20%).

## Output Template

```
Revenue Forecast (base case)

Current MRR: $[X]  |  Monthly growth: [+X%]  |  Churn: [X%]

| Month | MRR (worst) | MRR (base) | MRR (best) |
|-------|-------------|------------|------------|
| +3 | | | |
| +6 | | | |
| +12 | | | |

ARR run-rate (12mo base): $[X]
Key assumption risks: [list]
```

State all assumptions explicitly. Forecast quality degrades past 6 months.
