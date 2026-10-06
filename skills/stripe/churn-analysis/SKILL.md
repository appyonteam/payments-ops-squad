---
name: churn-analysis
description: "Analyzes Stripe subscription churn — cancellations, ended subs, voluntary vs involuntary signals, and period-over-period trends. Use when the user mentions \"churn\", \"cancellations\", \"subs leaving\", \"retention\", or \"why are we losing subscribers\". Pair with past-due-dunning for payment-driven churn."
metadata:
  version: 1.0.0
---

> Adapted by Vitor Dvorschi (Appyon) from [appeeky/stripe-skills](https://github.com/appeeky/stripe-skills) (MIT License, (c) 2026 Erencan).

# Churn Analysis

## Stripe MCP Setup

Requires **Stripe MCP** connected via OAuth or restricted key. Docs: https://docs.stripe.com/mcp

1. `GetMcpTools` with `server: "user-Stripe"` (or `plugin-stripe-stripe`) before any call
2. Prefer `stripe_api_search` → `stripe_api_details` → `stripe_api_read` for list/retrieve
3. **Always paginate** — `limit: 100`, follow `has_more` with `starting_after`
4. Amounts are in **cents** unless noted
5. Never expose secret keys in output

## Workflow

1. **Snapshot** active + past_due counts (today) via `GetSubscriptions`
2. **Canceled in period** — list subscriptions with `status: canceled` created or canceled in window
   - Use `search_stripe_resources`: `subscriptions:status:"canceled"` (note 100 cap — supplement with API list + filter)
3. **Classify churn**

| Type | Signal |
|------|--------|
| Voluntary | `cancellation_details.reason`, user canceled, feedback |
| Involuntary | Was `past_due` → `canceled`, `invoice.payment_failed` |
| Payment method | Debit/prepaid + failed charges |

4. Retrieve sample canceled subs: `GetSubscriptionsSubscriptionExposedId` with expand `cancellation_details`

## Churn Rate (approximate)

```
Monthly churn % ≈ canceled_in_30d / (active_start + new_in_30d) × 100
```

Benchmark: < 5% monthly good for SMB SaaS; < 2% excellent.

## Output Template

```
Churn Report ([period])

Canceled: [N]
Est. monthly churn: [X]%
Voluntary: [N] | Involuntary: [N]

Top cancel reasons (from cancellation_details):
1. [reason] — [n]

Recommendations:
1. [action] → skill: [name]
```

Cross-check `payment-failure-audit` if involuntary > 40% of churn.
