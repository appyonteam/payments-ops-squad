---
name: stripe-connect
description: "Guides Stripe Connect for marketplaces/platforms -- connected accounts, payouts to sellers, application fees, and onboarding. Use when the user mentions \"Connect\", \"marketplace payments\", \"pay out to sellers/creators\", \"connected accounts\", \"application fee\", or \"split payments\"."
metadata:
  version: 1.0.0
---

> Adapted by Vitor Dvorschi (Appyon) from [appeeky/stripe-skills](https://github.com/appeeky/stripe-skills) (MIT License, (c) 2026 Erencan).

# Stripe Connect

## Stripe MCP Setup

Requires **Stripe MCP** (https://docs.stripe.com/mcp). `GetMcpTools` before `CallMcpTool`. Paginate all lists (`limit: 100`, `starting_after` while `has_more`). Amounts in **cents**. Read-only for audits; confirm before writes.

## Account types

| Type | Control | Onboarding |
|------|---------|-----------|
| Express | Stripe-hosted onboarding + dashboard | Fastest |
| Standard | Seller's own Stripe account | Least liability |
| Custom | Full white-label | Most work/liability |

## Money flow

```
Customer pays -> platform charge -> application_fee_amount kept -> transfer/payout to connected account
```

Key params: `on_behalf_of`, `transfer_data.destination`, `application_fee_amount`.

## Workflow

1. `stripe_api_read` v2 accounts list / `GetAccounts` -- review connected accounts
2. Check charge type: direct / destination / separate charges & transfers
3. Verify onboarding completion (`requirements` on account)

## Output Template

```
Connect Overview

Account type: [Express/Standard/Custom]
Connected accounts: [n] ([active/pending])
Charge model: [destination/direct]
Application fee: [%/flat]

Onboarding gaps: [accounts with requirements due]
```

Use `search_stripe_documentation` for charge-type tradeoffs and liability.
