---
name: checkout-conversion
description: "Analyzes Stripe Checkout sessions — completion rate, abandonment, mode, and subscription signups. Use when the user mentions \"checkout conversion\", \"checkout sessions\", \"signup funnel\", or \"why aren't people completing checkout\"."
metadata:
  version: 1.0.0
---

> Adapted by Vitor Dvorschi (Appyon) from [appeeky/stripe-skills](https://github.com/appeeky/stripe-skills) (MIT License, (c) 2026 Erencan).

# Checkout Conversion

## Stripe MCP Setup

Requires **Stripe MCP** connected via OAuth or restricted key. Docs: https://docs.stripe.com/mcp

1. `GetMcpTools` with `server: "user-Stripe"` (or `plugin-stripe-stripe`) before any call
2. Prefer `stripe_api_search` → `stripe_api_details` → `stripe_api_read` for list/retrieve
3. **Always paginate** — `limit: 100`, follow `has_more` with `starting_after`
4. Amounts are in **cents** unless noted
5. Never expose secret keys in output

## Workflow

1. `GetCheckoutSessions` — recent window, `limit: 100`, paginate
2. Segment by `status`: `complete` vs `expired` vs `open`
3. For `mode: subscription`, link `subscription` id
4. Compute:

```
Conversion % = complete / (complete + expired) × 100
```

5. Check `payment_status` on completed sessions

## Codebase Cross-Check

Search project for `/api/checkout`, `checkout.sessions.create`, `success_url`, `cancel_url`.

## Output Template

```
Checkout Funnel ([period])

Sessions: [total]
Completed: [n] ([%])
Expired: [n]
Open: [n]

Common issues:
- [missing customer reuse / double subscription risk]
- [no promotion code tracking]

Recommendations: ...
```
