---
name: stripe-security-audit
description: "Audits Stripe security posture -- API key hygiene, restricted keys, secret leakage, PCI scope, and webhook signature verification. Use when the user mentions \"Stripe security\", \"key management\", \"restricted keys\", \"secret leak\", \"PCI\", or \"is our Stripe setup secure\"."
metadata:
  version: 1.0.0
---

> Adapted by Vitor Dvorschi (Appyon) from [appeeky/stripe-skills](https://github.com/appeeky/stripe-skills) (MIT License, (c) 2026 Erencan).

# Stripe Security Audit

Combines codebase scan + account settings review.

## Codebase scan

Grep for leaked secrets: `sk_live`, `sk_test`, `rk_live`, the webhook signing secret prefix (`whsec` followed by an underscore), hardcoded keys outside env.

## Checklist

| Area | Check |
|------|-------|
| Secret keys | Only in env/secrets vault, never client or repo |
| Publishable key | `pk_` only on client (safe) |
| Restricted keys | Used for scoped/agent access, least privilege |
| Webhook | Signature verified with the endpoint signing secret, not skipped |
| PCI scope | Using Checkout/Elements (SAQ-A), not raw card handling |
| Logging | No full card / secret / client_secret in logs |
| Key rotation | Old keys revoked in Dashboard |

## Output Template

```
Security Audit

Critical:
- [leaked/hardcoded key at file:line]
Harden:
- [use restricted key for X]
OK:
- [Checkout keeps PCI scope minimal]

Immediate: [rotate/remove any exposed key]
```

If a live secret key is found in the repo, advise **rotating it immediately** in the Dashboard.
