---
name: cohort-retention
description: "Builds subscriber cohort retention and revenue-retention tables grouped by signup month from Stripe data. Use when the user mentions \"cohort\", \"retention curve\", \"LTV curve\", \"how long do subscribers stay\", or \"retention by signup month\". For overall churn, see churn-analysis."
metadata:
  version: 1.0.0
---

> Adapted by Vitor Dvorschi (Appyon) from [appeeky/stripe-skills](https://github.com/appeeky/stripe-skills) (MIT License, (c) 2026 Erencan).

# Cohort Retention

## Stripe MCP Setup

Requires **Stripe MCP** (https://docs.stripe.com/mcp). `GetMcpTools` before `CallMcpTool`. Paginate all lists (`limit: 100`, `starting_after` while `has_more`). Amounts in **cents**. Read-only for audits; confirm before writes.

## Workflow

1. List subscriptions (all statuses) with `created` and `canceled_at`/`ended_at`
2. Bucket by signup month (`created`)
3. For each cohort, compute % still active at month 1, 2, 3...
4. Optionally weight by MRR for **revenue retention**

## Output Template

```
Cohort Retention (logo)

| Cohort | Size | M1 | M2 | M3 | M6 |
|--------|------|----|----|----|----|
| YYYY-MM | | | | | |

Revenue retention (NRR) latest cohort: [X]%
Insight: [where the biggest drop occurs]
```

Flag the month with steepest drop -- that's the retention leak to fix (route to churn-analysis or onboarding).
