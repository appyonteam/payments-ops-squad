---
name: stripe-integration-review
description: "Reviews Stripe integration code for correctness -- idempotency, error handling, API version pinning, webhook signature checks, and race conditions. Use when the user asks to \"review Stripe code\", \"audit our Stripe integration\", or mentions integration bugs, double-charging, or race conditions. For security specifically, see stripe-security-audit."
metadata:
  version: 1.0.0
---

> Adapted by Vitor Dvorschi (Appyon) from [appeeky/stripe-skills](https://github.com/appeeky/stripe-skills) (MIT License, (c) 2026 Erencan).

# Stripe Integration Review

Reviews the **codebase** (not just live data). Grep the repo for Stripe usage, then audit.

## Search targets

`new Stripe(`, `stripe.subscriptions`, `stripe.checkout`, `stripe.webhooks`, `apiVersion`, `idempotencyKey`.

## Review Checklist

| Area | Check |
|------|-------|
| API version | Pinned explicitly, not floating |
| Idempotency | `idempotencyKey` on create calls (retries safe) |
| Webhooks | Signature verified with `constructEvent` |
| Race conditions | Existing-subscription check before create (no double-bill) |
| Error handling | Stripe errors caught by type, user-friendly messages |
| Amounts | Cents, no float rounding bugs |
| Secrets | Key from env, never hardcoded |
| Proration | `proration_behavior` set intentionally on updates |

## Output Template

```
Integration Review

Critical:
- [file:line] -- [issue] -> [fix]
Improve:
- ...
Good:
- ...

Top fix: [highest-risk item]
```

Reference live behavior with MCP only to confirm suspicions (e.g. duplicate subs via `active-subscriptions-audit`).
