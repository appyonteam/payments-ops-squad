---
name: customer-portal-setup
description: "Audits and recommends Stripe Customer Portal configuration — payment method updates, cancellation flow, plan changes. Use when the user mentions \"customer portal\", \"billing portal\", \"update payment method\", or \"self-serve subscription management\"."
metadata:
  version: 1.0.0
---

> Adapted by Vitor Dvorschi (Appyon) from [appeeky/stripe-skills](https://github.com/appeeky/stripe-skills) (MIT License, (c) 2026 Erencan).

# Customer Portal Setup

## Stripe MCP Setup

Requires **Stripe MCP** connected via OAuth or restricted key. Docs: https://docs.stripe.com/mcp

1. `GetMcpTools` with `server: "user-Stripe"` (or `plugin-stripe-stripe`) before any call
2. Prefer `stripe_api_search` → `stripe_api_details` → `stripe_api_read` for list/retrieve
3. **Always paginate** — `limit: 100`, follow `has_more` with `starting_after`
4. Amounts are in **cents** unless noted
5. Never expose secret keys in output

## Workflow

1. `GetBillingPortalConfigurations` — list active configs
2. Verify features enabled:
   - `payment_method_update`
   - `invoice_history`
   - `subscription_cancel` (with retention offers if available)
   - `subscription_update` / proration behavior

## Codebase

Search: `billingPortal.sessions.create`, `customer_portal`, Stripe Portal URL in settings.

## Output Template

```
Customer Portal Audit

Portal enabled: yes/no
Features:
| Feature | Enabled | Recommendation |

Gap: [e.g. no payment method update → past_due recovery suffers]
```

Pair with `past-due-dunning` for recovery playbook.
