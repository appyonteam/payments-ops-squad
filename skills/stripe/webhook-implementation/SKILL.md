---
name: webhook-implementation
description: "Implements or fixes Stripe webhook handlers -- signature verification, event routing, idempotency, and retry-safe processing. Use when the user wants to \"add a webhook handler\", \"handle stripe events\", \"fix webhook\", or process specific events. For delivery health audit, see webhook-reliability."
metadata:
  version: 1.0.0
---

> Adapted by Vitor Dvorschi (Appyon) from [appeeky/stripe-skills](https://github.com/appeeky/stripe-skills) (MIT License, (c) 2026 Erencan).

# Webhook Implementation

Builds robust Stripe webhook handlers. Match the project's stack or ask users (Next.js route, Express, Supabase edge function).

## Must-haves

1. **Raw body** for signature verification (no JSON pre-parse)
2. `stripe.webhooks.constructEvent(body, sig, secret)`
3. **Idempotency** -- dedupe by `event.id` (store processed IDs)
4. Return `200` fast; heavy work async
5. Handle only subscribed events; ignore rest gracefully

## Core events (subscription SaaS)

| Event | Handler action |
|-------|----------------|
| `checkout.session.completed` | Provision access, save customer/sub IDs |
| `customer.subscription.updated` | Sync plan + status |
| `customer.subscription.deleted` | Revoke access |
| `invoice.payment_failed` | Trigger dunning email/banner |
| `invoice.paid` | Confirm renewal |

## Pattern (pseudocode)

```
event = constructEvent(rawBody, sig, secret)
if alreadyProcessed(event.id): return 200
switch event.type: ...handle...
markProcessed(event.id)
return 200
```

## Verify

Use Stripe CLI `stripe listen` / `stripe trigger`, or check `webhook-reliability` after deploy.
