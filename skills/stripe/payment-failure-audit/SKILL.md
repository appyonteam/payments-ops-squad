---
name: payment-failure-audit
description: "Audits failed Stripe payments — declined charges, PaymentIntents, invoice failures, decline codes, and failure rates. Use when the user asks \"how many payments failed\", \"decline reasons\", \"card declined\", or \"payment failure rate\"."
metadata:
  version: 1.0.0
---

> Adapted by Vitor Dvorschi (Appyon) from [appeeky/stripe-skills](https://github.com/appeeky/stripe-skills) (MIT License, (c) 2026 Erencan).

# Payment Failure Audit

## Stripe MCP Setup

Requires **Stripe MCP** connected via OAuth or restricted key. Docs: https://docs.stripe.com/mcp

1. `GetMcpTools` with `server: "user-Stripe"` (or `plugin-stripe-stripe`) before any call
2. Prefer `stripe_api_search` → `stripe_api_details` → `stripe_api_read` for list/retrieve
3. **Always paginate** — `limit: 100`, follow `has_more` with `starting_after`
4. Amounts are in **cents** unless noted
5. Never expose secret keys in output

## Workflow

1. **Recent failed charges** — `GetCharges` with filter or search:
   - `search_stripe_resources`: `charges:status:"failed"` (paginate if possible)
2. **Failed PaymentIntents** — `GetPaymentIntents` status `requires_payment_method` or failed
3. **Open invoices** — `GetInvoices` with `status: open` and `subscription` set
4. Group failures by:
   - `outcome.reason` / decline code
   - `card.funding`
   - `card.country`
   - Wallet vs direct card

## Common Decline Reasons

| Code / reason | Typical fix |
|---------------|-------------|
| `insufficient_funds` | Debit balance — dunning email |
| `card_declined` | Generic — retry + update PM |
| `expired_card` | Expiring card email |
| `authentication_required` | Enable 3DS on setup |
| Radar block | Review Radar rules |

## Output Template

```
Payment Failures ([period])

Total failed: [N] | $[amount]
Failure rate: [X]% of attempts

By reason:
| Reason | Count | % |

By card funding:
| funding | Count |

Top recommendations:
1. ...
```

Link to `radar-fraud-rules` if `blocked` or `highest` risk level appears in outcomes.
