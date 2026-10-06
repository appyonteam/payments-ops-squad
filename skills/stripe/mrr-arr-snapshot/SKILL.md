---
name: mrr-arr-snapshot
description: "Computes current MRR, ARR, and revenue breakdown from active Stripe subscriptions — by plan, interval, and currency. Use when the user asks \"what is our MRR\", \"monthly recurring revenue\", \"ARR\", \"how much recurring revenue\", or \"revenue by plan\". For full health check, see stripe-health-dashboard. For churn impact, see churn-analysis."
metadata:
  version: 1.0.0
---

> Adapted by Vitor Dvorschi (Appyon) from [appeeky/stripe-skills](https://github.com/appeeky/stripe-skills) (MIT License, (c) 2026 Erencan).

# MRR & ARR Snapshot

Calculate **normalized monthly recurring revenue** from Stripe subscription data.

## Stripe MCP Setup

Requires **Stripe MCP** connected via OAuth or restricted key. Docs: https://docs.stripe.com/mcp

1. `GetMcpTools` with `server: "user-Stripe"` (or `plugin-stripe-stripe`) before any call
2. Prefer `stripe_api_search` → `stripe_api_details` → `stripe_api_read` for list/retrieve
3. **Always paginate** — `limit: 100`, follow `has_more` with `starting_after`
4. Amounts are in **cents** unless noted
5. Never expose secret keys in output

## Workflow

1. List all `active` subscriptions — paginate until `has_more: false`
   - `GetSubscriptions` with `expand: ["data.items.data.price"]`, `status: active`, `limit: 100`
2. Optionally include `past_due` in "MRR at risk" (label separately)
3. For each subscription item, normalize to monthly MRR:

| Interval | Monthly MRR per unit |
|----------|---------------------|
| month | `unit_amount × quantity / interval_count` |
| year | `unit_amount × quantity / (12 × interval_count)` |
| week | `unit_amount × quantity × 52 / (12 × interval_count)` |

4. Group by `price.id` and product name
5. Sum → **MRR**; multiply by 12 → **ARR**

## Output Template

```
MRR Snapshot (as of [date])

Active subscriptions: [N]
MRR (active only):     $[X]
ARR:                   $[X × 12]
Past due MRR at risk:  $[Y] ([n] subs) — optional

By plan:
| Subs | Plan | Unit price | MRR |
|------|------|------------|-----|

Notes:
- [annual plans normalized to monthly]
- [multi-item subs counted once per sub, sum line items]
```

## Pitfalls

- Search API caps at 100 — use `GetSubscriptions` with pagination
- `trialing` subs: exclude from paid MRR unless user asks for "pipeline MRR"
- Multi-currency: report per currency or convert with stated FX rate
