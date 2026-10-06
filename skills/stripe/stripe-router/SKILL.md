---
name: stripe-router
description: "Single entry point that routes any Stripe billing, subscription, MRR, churn, payment failure, dunning, Radar fraud, checkout, invoice, payout, webhook, or pricing question to the correct specialist skill. Use FIRST when the user mentions Stripe, MRR, ARR, subscriptions, churn, past due, failed payment, Radar, checkout, invoices, payouts, or billing — but the right skill is not obvious. Triggers: \"/payments-ops-squad:pay-ask\", \"stripe help\", \"billing health\", \"how is revenue\". Skip when user explicitly invokes a skill (e.g. /mrr-arr-snapshot)."
metadata:
  version: 1.0.0
---

> Adapted by Vitor Dvorschi (Appyon) from [appeeky/stripe-skills](https://github.com/appeeky/stripe-skills) (MIT License, (c) 2026 Erencan).

# Stripe Router

Route natural-language Stripe requests to **one** specialist skill (max 3). Announce `→ Loading: <skill-name>` then invoke the skill `<skill-name>` by name. Do not answer yourself.

## Routing Table

| Intent / phrase | Route to |
|---|---|
| MRR, ARR, monthly revenue, recurring revenue snapshot | `mrr-arr-snapshot` |
| How many subs, active subscriptions, trialing, canceled counts | `active-subscriptions-audit` |
| Churn rate, cancellations, retention, logo churn | `churn-analysis` |
| Past due, unpaid, failed renewal, dunning, smart retries | `past-due-dunning` |
| Payment failed, decline, card declined, failure reasons | `payment-failure-audit` |
| Prepaid, virtual card, disposable card, debit vs credit | `card-funding-risk` |
| Radar, fraud, block rules, 3DS, high risk | `radar-fraud-rules` |
| Products, prices, plans, what we sell, price IDs | `pricing-products-audit` |
| Checkout conversion, checkout sessions, signup funnel | `checkout-conversion` |
| Invoices, open invoices, billing history | `invoice-revenue-audit` |
| Customer portal, update payment method, self-serve billing | `customer-portal-setup` |
| Webhooks failing, webhook delivery, event sync | `webhook-reliability` |
| Payment failed email, dunning email, billing emails | `email-dunning-setup` |
| Coupons, promo codes, discounts, promotions | `coupon-promotion-audit` |
| Disputes, chargebacks, refunds | `dispute-refund-audit` |
| Balance, payouts, cash available, treasury | `payout-balance-report` |
| Upgrade, downgrade, plan change, proration | `subscription-plan-changes` |
| Full billing health check, weekly Stripe review | `stripe-health-dashboard` |
| First time / set up context doc | `stripe-billing-context` |
| Revenue forecast, MRR projection, ARR run-rate, growth trajectory | `revenue-forecasting` |
| Cohort, retention curve, LTV curve, retention by signup month | `cohort-retention` |
| Price test, raise prices, grandfathering, elasticity | `pricing-experiments` |
| Expansion revenue, upsell, NRR, add-ons, grow accounts | `upsell-expansion` |
| One customer, customer detail, LTV lookup, cus_/email | `customer-360` |
| Segment customers, by country/plan, best customers, value tiers | `customer-segmentation` |
| Revenue recognition, deferred revenue, accrual, MRR vs cash | `revenue-recognition` |
| Stripe Tax, sales tax, VAT, GST, nexus | `tax-compliance` |
| Reconciliation, payout vs bank, Stripe fees, balance transactions | `financial-reconciliation` |
| Review Stripe code, audit integration, double-charging, idempotency | `stripe-integration-review` |
| Add/fix webhook handler, handle events, signature verification | `webhook-implementation` |
| Add checkout, build payment flow, integrate payments, paywall | `checkout-implementation` |
| Stripe security, key management, secret leak, PCI, restricted keys | `stripe-security-audit` |
| Connect, marketplace, payouts to sellers, application fee, split payments | `stripe-connect` |
| Usage-based, metered, pay per use, meters, credits, overage | `usage-based-billing` |

## Multi-Skill Chains

| Request | Order |
|---|---|
| "How is the business doing?" | `stripe-health-dashboard` |
| "Why is churn up?" | `churn-analysis` → `past-due-dunning` → `payment-failure-audit` |
| "Block virtual cards" | `card-funding-risk` → `radar-fraud-rules` |
| "Revenue dropped" | `mrr-arr-snapshot` → `churn-analysis` → `checkout-conversion` |
| "Fix failed payments" | `payment-failure-audit` → `email-dunning-setup` → `past-due-dunning` |
| "Where will revenue be" | `mrr-arr-snapshot` → `revenue-forecasting` |
| "Improve retention" | `cohort-retention` → `churn-analysis` → `upsell-expansion` |
| "Grow existing accounts" | `customer-segmentation` → `upsell-expansion` → `pricing-experiments` |
| "Build a payment flow" | `checkout-implementation` → `webhook-implementation` → `stripe-security-audit` |
| "Audit our Stripe code" | `stripe-integration-review` → `stripe-security-audit` → `webhook-reliability` |
| "Accounting / close the books" | `revenue-recognition` → `financial-reconciliation` → `tax-compliance` |
| "Launch a marketplace" | `stripe-connect` → `checkout-implementation` → `payout-balance-report` |

## Handoff Template

```
→ Routing to: <skill-name>
   Why: <one line>
```

Check for `stripe-billing-context.md` before deep analysis; suggest creating via `stripe-billing-context` if missing.
