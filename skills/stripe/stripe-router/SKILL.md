---
name: stripe-router
description: "Single entry point that routes any Stripe billing, subscription, MRR, churn, payment failure, dunning, Radar fraud, checkout, invoice, payout, webhook, or pricing question to the correct specialist skill. Use FIRST when the user mentions Stripe, MRR, ARR, subscriptions, churn, past due, failed payment, Radar, checkout, invoices, payouts, or billing — but the right skill is not obvious. Triggers: \"/payments-ops-squad:pay-ask\", \"stripe help\", \"billing health\", \"how is revenue\". Skip when user explicitly invokes a skill (e.g. /mrr-arr-snapshot)."
metadata:
  version: 1.0.0
---

> Adapted by Vitor Dvorschi (Appyon) from [appeeky/stripe-skills](https://github.com/appeeky/stripe-skills) (MIT License, (c) 2026 Erencan).

# Stripe Router

Route natural-language Stripe requests to **one** specialist skill (max 3). Announce `→ Loading: <skill-name>` then invoke the skill `<skill-name>` by name. Do not answer yourself. Exception: a row with "(no skill)" has nothing to load; forward the request directly to the agent named in the Agent column.

## Routing Table

The Agent column names the specialist agent that owns each skill; `stripe-router` itself is the entry point and has no owner. In Claude Code, hand deep or multi-skill work to that agent.

| Intent / phrase | Route to | Agent |
|---|---|---|
| MRR, ARR, monthly revenue, recurring revenue snapshot | `mrr-arr-snapshot` | `stripe-billing` |
| How many subs, active subscriptions, trialing, canceled counts | `active-subscriptions-audit` | `stripe-billing` |
| Churn rate, cancellations, retention, logo churn | `churn-analysis` | `stripe-billing` |
| Past due, unpaid, failed renewal, dunning, smart retries | `past-due-dunning` | `stripe-billing` |
| Payment failed, decline, card declined, failure reasons | `payment-failure-audit` | `stripe-payments` |
| Prepaid, virtual card, disposable card, debit vs credit | `card-funding-risk` | `stripe-risk` |
| Radar, fraud, block rules, 3DS, high risk | `radar-fraud-rules` | `stripe-risk` |
| Products, prices, plans, what we sell, price IDs | `pricing-products-audit` | `stripe-billing` |
| Checkout conversion, checkout sessions, signup funnel | `checkout-conversion` | `stripe-payments` |
| Invoices, open invoices, billing history | `invoice-revenue-audit` | `stripe-billing` |
| Customer portal, update payment method, self-serve billing | `customer-portal-setup` | `stripe-billing` |
| Webhooks failing, webhook delivery, event sync | `webhook-reliability` | `stripe-payments` |
| Payment failed email, dunning email, billing emails | `email-dunning-setup` | `stripe-billing` |
| Coupons, promo codes, discounts, promotions | `coupon-promotion-audit` | `stripe-billing` |
| Disputes, chargebacks, refunds | `dispute-refund-audit` | `stripe-disputes` |
| Early Fraud Warning, fraud warning, TC40 | (no skill) | `stripe-disputes` |
| Balance, payouts, cash available, treasury | `payout-balance-report` | `stripe-finance` |
| Upgrade, downgrade, plan change, proration | `subscription-plan-changes` | `stripe-billing` |
| Full billing health check, weekly Stripe review | `stripe-health-dashboard` | `stripe-billing` |
| First time / set up context doc | `stripe-billing-context` | `stripe-billing` |
| Revenue forecast, MRR projection, ARR run-rate, growth trajectory | `revenue-forecasting` | `stripe-finance` |
| Cohort, retention curve, LTV curve, retention by signup month | `cohort-retention` | `stripe-billing` |
| Price test, raise prices, grandfathering, elasticity | `pricing-experiments` | `stripe-billing` |
| Expansion revenue, upsell, NRR, add-ons, grow accounts | `upsell-expansion` | `stripe-billing` |
| One customer, customer detail, LTV lookup, cus_/email | `customer-360` | `stripe-billing` |
| Segment customers, by country/plan, best customers, value tiers | `customer-segmentation` | `stripe-billing` |
| Revenue recognition, deferred revenue, accrual, MRR vs cash | `revenue-recognition` | `stripe-finance` |
| Stripe Tax, sales tax, VAT, GST, nexus | `tax-compliance` | `stripe-finance` |
| Reconciliation, payout vs bank, Stripe fees, balance transactions | `financial-reconciliation` | `stripe-finance` |
| Review Stripe code, audit integration, double-charging, idempotency | `stripe-integration-review` | `stripe-payments` |
| Add/fix webhook handler, handle events, signature verification | `webhook-implementation` | `stripe-payments` |
| Add checkout, build payment flow, integrate payments, paywall | `checkout-implementation` | `stripe-payments` |
| Stripe security, key management, secret leak, PCI, restricted keys | `stripe-security-audit` | `stripe-risk` |
| Connect, marketplace, payouts to sellers, application fee, split payments | `stripe-connect` | `stripe-finance` |
| Usage-based, metered, pay per use, meters, credits, overage | `usage-based-billing` | `stripe-billing` |

Webhook rows: implementation in `stripe-payments`, posture audit in `stripe-risk`.

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
