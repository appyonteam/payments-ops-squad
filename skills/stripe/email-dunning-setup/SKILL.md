---
name: email-dunning-setup
description: "Audits payment-failed and dunning email flows — Stripe built-in emails vs custom webhook emails. Use when the user asks \"payment failed email\", \"dunning emails\", \"billing emails setup\", or \"notify users when card fails\"."
metadata:
  version: 1.0.0
---

> Adapted by Vitor Dvorschi (Appyon) from [appeeky/stripe-skills](https://github.com/appeeky/stripe-skills) (MIT License, (c) 2026 Erencan).

# Email & Dunning Setup

## Two Layers

### 1. Stripe-native (Dashboard)

Settings → Billing → **Customer emails**:
- Failed payment
- Expiring card
- Trial ending
- Receipts

Verify toggles ON for production.

### 2. Custom (your app)

Webhook `invoice.payment_failed` → send email with Portal link.

## Codebase Audit

Grep: `payment_failed`, `payment-failed`, `invoice.payment_failed`, `sendPaymentFailed`, Resend/SendGrid/Postmark.

## MCP + Code Workflow

1. Confirm webhook handler exists (`webhook-reliability`)
2. Sample past_due subs (`past-due-dunning`) — were emails sent? (logs/DB)
3. Customer Portal URL in email template?

## Output Template

```
Dunning Email Audit

Stripe emails: [on/off per type]
Custom email on payment_failed: yes/no
Portal link in email: yes/no
Gap: [description]

Recommended sequence:
Day 0 fail → Stripe retry
Day 3 → custom email + portal
Day 7 → final notice
```
