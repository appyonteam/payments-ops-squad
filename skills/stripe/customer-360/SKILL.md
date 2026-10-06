---
name: customer-360
description: "Builds a full profile for a single Stripe customer -- subscriptions, LTV, invoice history, payment health, discounts, and churn risk. Use when the user asks about \"this customer\", \"customer detail\", \"look up customer\", \"customer LTV\", or gives a customer/email/sub ID. For whole-base segments, see customer-segmentation."
metadata:
  version: 1.0.0
---

> Adapted by Vitor Dvorschi (Appyon) from [appeeky/stripe-skills](https://github.com/appeeky/stripe-skills) (MIT License, (c) 2026 Erencan).

# Customer 360

## Stripe MCP Setup

Requires **Stripe MCP** (https://docs.stripe.com/mcp). `GetMcpTools` before `CallMcpTool`. Paginate all lists (`limit: 100`, `starting_after` while `has_more`). Amounts in **cents**. Read-only for audits; confirm before writes.

## Workflow

1. Resolve customer: `search_stripe_resources` by email, or `fetch_stripe_resources` by `cus_`/`sub_` id
2. Pull:
   - Customer object (created, currency, delinquent)
   - Subscriptions (status, plan, MRR, tenure)
   - Invoices (paid total = LTV proxy, open/uncollectible)
   - Default payment method (brand, funding, expiry)
   - Discounts / coupons

## Churn Risk Signals

| Signal | Risk |
|--------|------|
| `delinquent: true` | High |
| past_due sub | High |
| prepaid/expiring card | Medium |
| Long tenure, active | Low (protect) |

## Output Template

```
Customer 360 -- [email / cus_id]

Tenure: [N months]  |  Status: [active/past_due]
Lifetime paid: $[X]  |  Current MRR: $[Y]
Payment: [brand last4, funding, exp]
Churn risk: [Low/Med/High] -- [reason]

Recent invoices:
| Date | Amount | Status |

Recommended action: [protect / recover / upsell]
```

Never print full card numbers or PII beyond last4 + country.
