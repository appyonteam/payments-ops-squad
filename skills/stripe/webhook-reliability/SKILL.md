---
name: webhook-reliability
description: "Audits Stripe webhook delivery health — failed events, missing handlers, and idempotency risks. Use when the user mentions \"webhooks\", \"stripe webhook failing\", \"subscription not syncing\", or \"checkout completed but no access\"."
metadata:
  version: 1.0.0
---

> Adapted by Vitor Dvorschi (Appyon) from [appeeky/stripe-skills](https://github.com/appeeky/stripe-skills) (MIT License, (c) 2026 Erencan).

# Webhook Reliability

## Stripe MCP Setup

Requires **Stripe MCP** connected via OAuth or restricted key. Docs: https://docs.stripe.com/mcp

1. `GetMcpTools` with `server: "user-Stripe"` (or `plugin-stripe-stripe`) before any call
2. Prefer `stripe_api_search` → `stripe_api_details` → `stripe_api_read` for list/retrieve
3. **Always paginate** — `limit: 100`, follow `has_more` with `starting_after`
4. Amounts are in **cents** unless noted
5. Never expose secret keys in output

## Workflow

1. Dashboard: Developers → Webhooks → recent deliveries (user may paste errors)
2. Codebase grep: `stripe.webhooks`, `checkout.session.completed`, `customer.subscription`, `invoice.payment_failed`
3. Required events for subscription SaaS:

| Event | Purpose |
|-------|---------|
| `checkout.session.completed` | Provision access |
| `customer.subscription.updated` | Plan/status sync |
| `customer.subscription.deleted` | Revoke access |
| `invoice.payment_failed` | Dunning email / banner |
| `invoice.paid` | Confirm renewal |

## Output Template

```
Webhook Audit

Endpoint(s): [urls from code]
Handled events: [list]
Missing critical: [list]
Failed deliveries (if known): [summary]

Fix priority:
1. ...
```
