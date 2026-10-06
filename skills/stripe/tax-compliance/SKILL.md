---
name: tax-compliance
description: "Audits Stripe Tax configuration, tax collected, nexus/registration coverage, and VAT/GST/sales-tax handling. Use when the user mentions \"Stripe Tax\", \"sales tax\", \"VAT\", \"GST\", \"tax compliance\", \"nexus\", or \"am I collecting tax correctly\"."
metadata:
  version: 1.0.0
---

> Adapted by Vitor Dvorschi (Appyon) from [appeeky/stripe-skills](https://github.com/appeeky/stripe-skills) (MIT License, (c) 2026 Erencan).

# Tax Compliance

## Stripe MCP Setup

Requires **Stripe MCP** (https://docs.stripe.com/mcp). `GetMcpTools` before `CallMcpTool`. Paginate all lists (`limit: 100`, `starting_after` while `has_more`). Amounts in **cents**. Read-only for audits; confirm before writes.

## Workflow

1. `GetTaxSettings` -- is automatic tax enabled? default behavior?
2. Check subscriptions/invoices for `automatic_tax.enabled` and `tax` amounts
3. Identify countries with sales but no tax collected -> possible nexus gap

## Checklist

- [ ] Stripe Tax enabled (Dashboard -> Tax)
- [ ] Registrations added for nexus countries/states
- [ ] Products have tax codes
- [ ] Checkout has automatic tax enabled
- [ ] Prices marked tax-inclusive or exclusive intentionally

## Output Template

```
Tax Compliance Audit

Stripe Tax: enabled / disabled
Tax collected ([period]): $[X]
Countries with sales: [list]
Registrations on file: [list]
Gaps: [countries with sales but no registration]

Action: [register in X, enable automatic tax on checkout]
```

Use `search_stripe_documentation` for country-specific thresholds. Not legal/tax advice -- recommend an accountant for registration decisions.
