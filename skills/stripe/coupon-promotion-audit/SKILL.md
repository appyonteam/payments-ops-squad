---
name: coupon-promotion-audit
description: "Audits Stripe coupons and promotion codes — active discounts, redemptions, and revenue impact. Use when the user mentions \"coupons\", \"promo codes\", \"discounts\", or \"promotion usage\"."
metadata:
  version: 1.0.0
---

> Adapted by Vitor Dvorschi (Appyon) from [appeeky/stripe-skills](https://github.com/appeeky/stripe-skills) (MIT License, (c) 2026 Erencan).

# Coupon & Promotion Audit

## Stripe MCP Setup

Requires **Stripe MCP** connected via OAuth or restricted key. Docs: https://docs.stripe.com/mcp

1. `GetMcpTools` with `server: "user-Stripe"` (or `plugin-stripe-stripe`) before any call
2. Prefer `stripe_api_search` → `stripe_api_details` → `stripe_api_read` for list/retrieve
3. **Always paginate** — `limit: 100`, follow `has_more` with `starting_after`
4. Amounts are in **cents** unless noted
5. Never expose secret keys in output

## Workflow

1. `GetCoupons` — `limit: 100`
2. `GetPromotionCodes` — active codes
3. On active subscriptions, check `discount` / `discounts` array
4. Estimate discounted MRR impact

## Output Template

```
Promotions ([date])

Active coupons: [n]
Active promotion codes: [n]
Subs with discount: [n] ([%] of active)

| Code | % off | Redemptions | Est. MRR impact |

Risk: [lifetime discounts on annual plans]
```
