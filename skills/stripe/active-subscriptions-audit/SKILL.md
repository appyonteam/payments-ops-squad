---
name: active-subscriptions-audit
description: "Audits Stripe subscription counts and status mix — active, trialing, past_due, canceled, paused. Use when the user asks \"how many subscribers\", \"subscription count\", \"active subs\", \"trialing users\", or status breakdown. For MRR dollars, see mrr-arr-snapshot."
metadata:
  version: 1.0.0
---

> Adapted by Vitor Dvorschi (Appyon) from [appeeky/stripe-skills](https://github.com/appeeky/stripe-skills) (MIT License, (c) 2026 Erencan).

# Active Subscriptions Audit

## Stripe MCP Setup

Requires **Stripe MCP** connected via OAuth or restricted key. Docs: https://docs.stripe.com/mcp

1. `GetMcpTools` with `server: "user-Stripe"` (or `plugin-stripe-stripe`) before any call
2. Prefer `stripe_api_search` → `stripe_api_details` → `stripe_api_read` for list/retrieve
3. **Always paginate** — `limit: 100`, follow `has_more` with `starting_after`
4. Amounts are in **cents** unless noted
5. Never expose secret keys in output

## Workflow

For each status, paginate `GetSubscriptions`:

| Status | Meaning |
|--------|---------|
| `active` | Paying, current |
| `trialing` | In trial |
| `past_due` | Payment failed, not canceled yet |
| `canceled` | Ended (use date filter if needed) |
| `paused` | Collection paused |
| `unpaid` | Retries exhausted |

```
stripe_api_read GetSubscriptions { status: "active", limit: 100 }
```

Repeat for `trialing`, `past_due`, `unpaid`, `paused`.

## Metrics

| Metric | Formula |
|--------|---------|
| Paid subs | active + past_due (optional) |
| Trial pipeline | trialing count |
| At-risk subs | past_due + unpaid |
| Line items per sub | items.data.length (multi-product subs) |

## Output Template

```
Subscription Status ([date])

| Status | Count | % of total |
|--------|-------|------------|
| Active | | |
| Trialing | | |
| Past due | | |
| Unpaid | | |

Multi-product subs: [N] subs with 2+ line items
```

Flag if `past_due` > 5% of active — investigate with `past-due-dunning`.
