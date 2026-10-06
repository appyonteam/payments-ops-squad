---
name: past-due-dunning
description: "Investigates past_due and unpaid Stripe subscriptions — failed invoice attempts, MRR at risk, and dunning/retry status. Use when the user mentions \"past due\", \"unpaid subs\", \"dunning\", \"smart retries\", \"grace period\", or \"recover failed renewals\"."
metadata:
  version: 1.0.0
---

> Adapted by Vitor Dvorschi (Appyon) from [appeeky/stripe-skills](https://github.com/appeeky/stripe-skills) (MIT License, (c) 2026 Erencan).

# Past Due & Dunning

## Stripe MCP Setup

Requires **Stripe MCP** connected via OAuth or restricted key. Docs: https://docs.stripe.com/mcp

1. `GetMcpTools` with `server: "user-Stripe"` (or `plugin-stripe-stripe`) before any call
2. Prefer `stripe_api_search` → `stripe_api_details` → `stripe_api_read` for list/retrieve
3. **Always paginate** — `limit: 100`, follow `has_more` with `starting_after`
4. Amounts are in **cents** unless noted
5. Never expose secret keys in output

## Workflow

1. `GetSubscriptions` with `status: past_due` and `status: unpaid` — paginate all
2. Expand `default_payment_method` and `latest_invoice`
3. Per sub record:
   - Plan(s) + MRR
   - `latest_invoice.attempt_count`, `amount_due`, `status`
   - Card: brand, last4, `funding`, country, wallet type
4. Sum **MRR at risk**

## Dunning Checklist (Dashboard)

- [ ] Smart Retries enabled (Billing → Revenue recovery)
- [ ] Customer emails: failed payment, card expiring
- [ ] Customer Portal: payment method update enabled
- [ ] Webhook: `invoice.payment_failed` handled in app

## Output Template

```
Past Due Report ([date])

| # | Sub | Plan | MRR | Attempts | Card | Country |
|---|-----|------|-----|----------|------|---------|

Total: [N] subs | $[MRR]/mo at risk
Funding mix: credit [n] | debit [n] | prepaid [n]

Priority actions:
1. [highest $ sub with most attempts]
```

Route email gaps to `email-dunning-setup`; card patterns to `card-funding-risk`.
