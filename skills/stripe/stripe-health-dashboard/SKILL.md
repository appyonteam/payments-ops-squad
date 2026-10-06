---
name: stripe-health-dashboard
description: "Full Stripe billing health check — MRR, subs, churn signals, past due, failures, disputes, and top actions. Use for \"Stripe health\", \"billing review\", \"weekly revenue check\", or executive snapshot. Orchestrates multiple specialist skills."
metadata:
  version: 1.0.0
---

> Adapted by Vitor Dvorschi (Appyon) from [appeeky/stripe-skills](https://github.com/appeeky/stripe-skills) (MIT License, (c) 2026 Erencan).

# Stripe Health Dashboard

Executive billing review. Run sub-analyses via MCP, synthesize one report.

## Stripe MCP Setup

Requires **Stripe MCP** connected via OAuth or restricted key. Docs: https://docs.stripe.com/mcp

1. `GetMcpTools` with `server: "user-Stripe"` (or `plugin-stripe-stripe`) before any call
2. Prefer `stripe_api_search` → `stripe_api_details` → `stripe_api_read` for list/retrieve
3. **Always paginate** — `limit: 100`, follow `has_more` with `starting_after`
4. Amounts are in **cents** unless noted
5. Never expose secret keys in output

## Run Order

1. `get_stripe_account_info`
2. **MRR** — follow `mrr-arr-snapshot` (active + past_due at risk)
3. **Subs** — `active-subscriptions-audit` status table
4. **Past due** — `past-due-dunning` top 5 by MRR
5. **Failures** — `payment-failure-audit` last 30d summary
6. **Card mix** — `card-funding-risk` active vs past_due
7. **Disputes** — open count from `GetDisputes`
8. **Balance** — available from `GetBalance`

## Output Template

```
Stripe Health — [Business] — [date]

## Headline
MRR: $[X] | Active subs: [N] | Past due: [n] ($[Y] at risk)

## Traffic lights
| Area | Status | Note |
|------|--------|------|
| MRR trend | 🟢/🟡/🔴 | |
| Churn / past due | | |
| Payment failures | | |
| Webhooks / emails | | manual/code check |
| Fraud / Radar | | |

## Top 3 actions this week
1.
2.
3.

## Drill-down skills
→ [skill-name] for details
```

Load `stripe-billing-context.md` if present for targets comparison.
