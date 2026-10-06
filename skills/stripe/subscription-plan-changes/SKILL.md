---
name: subscription-plan-changes
description: "Analyzes subscription upgrades, downgrades, prorations, and plan migrations in Stripe. Use when the user mentions \"upgrade\", \"downgrade\", \"plan change\", \"proration\", or \"switching tiers\"."
metadata:
  version: 1.0.0
---

> Adapted by Vitor Dvorschi (Appyon) from [appeeky/stripe-skills](https://github.com/appeeky/stripe-skills) (MIT License, (c) 2026 Erencan).

# Subscription Plan Changes

## Stripe MCP Setup

Requires **Stripe MCP** connected via OAuth or restricted key. Docs: https://docs.stripe.com/mcp

1. `GetMcpTools` with `server: "user-Stripe"` (or `plugin-stripe-stripe`) before any call
2. Prefer `stripe_api_search` → `stripe_api_details` → `stripe_api_read` for list/retrieve
3. **Always paginate** — `limit: 100`, follow `has_more` with `starting_after`
4. Amounts are in **cents** unless noted
5. Never expose secret keys in output

## Workflow

1. Review codebase checkout update path (`subscriptions.update` vs new checkout)
2. Sample recent `customer.subscription.updated` — compare `items` price changes
3. Check proration: `proration_behavior`, invoice line items for `proration`

## Anti-Patterns

- Creating **new** subscription instead of updating → double billing
- No `alreadyOnPlan` guard

## Output Template

```
Plan Change Audit

Update method: in-place / new checkout
Proration: [behavior]

Recent migrations (sample):
| Customer | From → To | Proration $ |

Recommendations: ...
```
