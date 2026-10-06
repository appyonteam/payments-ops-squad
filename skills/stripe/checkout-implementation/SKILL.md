---
name: checkout-implementation
description: "Implements Stripe payment flows -- Checkout Sessions, Payment Element, subscription signup, and customer reuse. Use when the user wants to \"add checkout\", \"build a payment flow\", \"integrate Stripe payments\", \"add a paywall\", or \"subscription signup\". For conversion analysis, see checkout-conversion."
metadata:
  version: 1.0.0
---

> Adapted by Vitor Dvorschi (Appyon) from [appeeky/stripe-skills](https://github.com/appeeky/stripe-skills) (MIT License, (c) 2026 Erencan).

# Checkout Implementation

Builds Stripe payment flows matched to the project stack.

## Choose the approach

| Need | Use |
|------|-----|
| Fastest, hosted | Stripe Checkout (`checkout.sessions.create`) |
| Embedded, custom UI | Payment Element + PaymentIntent/SetupIntent |
| Recurring | subscription mode |

## Checkout Session essentials

- mode: subscription
- line_items: price + quantity
- customer OR customer_email (reuse existing customer to avoid dupes)
- success_url / cancel_url
- allow_promotion_codes: true
- subscription_data metadata: user_id
- automatic_tax enabled (if using Stripe Tax)

## Critical rules

- **Reuse customer**: check for existing `stripe_customer_id`; for plan changes use `subscriptions.update` (proration), never a 2nd subscription
- Pass `user_id` in metadata for webhook provisioning
- Server-side price validation (whitelist price IDs)

## Verify

`stripe_implementation_planner` (MCP) for architecture; test with test cards; confirm via `webhook-implementation`.
