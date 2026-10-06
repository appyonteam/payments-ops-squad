---
name: card-funding-risk
description: "Analyzes Stripe payment method funding types — prepaid, debit, credit, unknown — across active and past_due subscriptions. Use when the user mentions \"prepaid cards\", \"virtual cards\", \"disposable cards\", \"debit churn\", or \"block card types\". Pair with radar-fraud-rules for blocking rules."
metadata:
  version: 1.0.0
---

> Adapted by Vitor Dvorschi (Appyon) from [appeeky/stripe-skills](https://github.com/appeeky/stripe-skills) (MIT License, (c) 2026 Erencan).

# Card Funding Risk

## Stripe MCP Setup

Requires **Stripe MCP** connected via OAuth or restricted key. Docs: https://docs.stripe.com/mcp

1. `GetMcpTools` with `server: "user-Stripe"` (or `plugin-stripe-stripe`) before any call
2. Prefer `stripe_api_search` → `stripe_api_details` → `stripe_api_read` for list/retrieve
3. **Always paginate** — `limit: 100`, follow `has_more` with `starting_after`
4. Amounts are in **cents** unless noted
5. Never expose secret keys in output

## Workflow

1. Paginate `GetSubscriptions` — statuses: `active`, `past_due`, `trialing`
2. Expand `data.default_payment_method`
3. Read `payment_method.card.funding`: `credit` | `debit` | `prepaid` | `unknown`
4. Cross-tab: funding × status (active vs past_due)

## MRR Normalization

Same as `mrr-arr-snapshot` — report prepaid/debit MRR separately.

## Blocking Options

| Approach | Catches | Misses |
|----------|---------|--------|
| Radar: `Block if :card_funding: = 'prepaid'` | Prepaid, many disposable | Virtual debit |
| Radar: 3DS on new cards | Fraud, some disposable | Low-balance debit |
| Webhook reject on `prepaid` | Post-checkout cleanup | After first charge |

Requires **Radar for Fraud Teams** for custom rules.

## Output Template

```
Card Funding Audit

| Status | Credit | Debit | Prepaid | Unknown |
|--------|--------|-------|---------|---------|

Past due with prepaid: [n] / [total past_due]
Active with prepaid: [n] / [total active]

Prepaid subs (detail):
| sub | last4 | country | MRR |

Recommendation: [block prepaid / 3DS / monitor debit past_due rate]
```
