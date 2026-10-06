---
name: pricing-products-audit
description: "Maps Stripe products and prices — plans, intervals, amounts, active vs archived, and which prices appear on live subscriptions. Use when the user asks \"what products do we sell\", \"price IDs\", \"pricing tiers\", \"plan structure\", or \"where does revenue go\"."
metadata:
  version: 1.0.0
---

> Adapted by Vitor Dvorschi (Appyon) from [appeeky/stripe-skills](https://github.com/appeeky/stripe-skills) (MIT License, (c) 2026 Erencan).

# Pricing & Products Audit

## Stripe MCP Setup

Requires **Stripe MCP** connected via OAuth or restricted key. Docs: https://docs.stripe.com/mcp

1. `GetMcpTools` with `server: "user-Stripe"` (or `plugin-stripe-stripe`) before any call
2. Prefer `stripe_api_search` → `stripe_api_details` → `stripe_api_read` for list/retrieve
3. **Always paginate** — `limit: 100`, follow `has_more` with `starting_after`
4. Amounts are in **cents** unless noted
5. Never expose secret keys in output

## Workflow

1. `GetProducts` — `active: true`, `limit: 100`
2. `GetPrices` — `active: true`, `type: recurring`, `limit: 100`
3. `GetSubscriptions` — `status: active` — count subs per `price.id`
4. Flag:
   - Orphan prices (no active subs)
   - Legacy prices still in use
   - Annual vs monthly mix

## Output Template

```
Product Catalog

| Product | Price ID | Amount | Interval | Active subs | MRR share |
|---------|----------|--------|----------|-------------|-----------|

Legacy / unused prices: [list]
Recommendation: [consolidate / archive / migrate]
```
