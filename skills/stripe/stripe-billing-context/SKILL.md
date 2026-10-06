---
name: stripe-billing-context
description: "Creates or updates a stripe-billing-context.md with business model, Stripe account, products/prices, webhook endpoints, email flows, and KPI targets. Use FIRST for a new Stripe account or when other skills need business context. Triggers: \"set up stripe context\", \"billing brief\", \"document our Stripe setup\"."
metadata:
  version: 1.0.0
---

> Adapted by Vitor Dvorschi (Appyon) from [appeeky/stripe-skills](https://github.com/appeeky/stripe-skills) (MIT License, (c) 2026 Erencan).

> This skill writes stripe-billing-context.md with account details; keep it out of version control.

# Stripe Billing Context

Produce `stripe-billing-context.md` in the workspace so every Stripe skill shares the same facts.

## Gather (ask or infer)

1. Business name + Stripe account (`get_stripe_account_info`)
2. Products & prices (`GetPrices`, `GetProducts` — active only)
3. Subscription model (monthly/annual, trials, add-ons)
4. Webhook endpoints (from codebase + Dashboard)
5. Customer Portal enabled? Billing emails configured?
6. KPI targets: MRR goal, acceptable churn, past-due threshold

## MCP Calls

```
get_stripe_account_info → {}
stripe_api_read GetProducts { parameters: { active: true, limit: 100 } }
stripe_api_read GetPrices { parameters: { active: true, limit: 100, type: recurring } }
```

## Output Template

```markdown
# Stripe Billing Context

## Account
- Display name:
- Account ID:
- Mode: live / test

## Revenue Model
- Primary product:
- Price tiers:
- Trials:
- Add-ons:

## Integrations
- Webhook URL:
- Events subscribed:
- Customer Portal:
- Payment failed emails:

## KPI Targets
| Metric | Target |
|--------|--------|
| MRR | |
| Monthly churn | < % |
| Past due subs | < N |
| Dunning recovery | > % |

## Notes
```

Re-run when pricing or webhook architecture changes.
