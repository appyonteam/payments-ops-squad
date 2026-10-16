> Status: draft. Not yet validated against a live Solidgate account.

# 12. Stripe vs Solidgate

Common rules: see `README.md`. Supports scenarios **C** (best connector when one of them is Stripe) and **E**. A mixed topic: involve the Solidgate specialists and the Stripe skills, with closing sections "SOLIDGATE SQUAD APPLIED" and "STRIPE SKILLS APPLIED".

## 1. Objective
Compare Stripe (processor, Radar, Billing, Connect) with Solidgate (orchestrator, PSP and in some cases acquirer, with its own anti-fraud, Billing and finance) across approval, risk, 3DS, billing, disputes, reporting and webhooks, without equating terms by name ("blocked", "decline", "Smart Retries", "dispute", "settlement"). It includes the case where Stripe sits behind Solidgate as a connector (the Solidgate settlement provider list includes Stripe).

## 2. Symptoms
- The same card is approved in one and declined in the other, with different codes.
- A risk block with a different label (Radar vs Antifraud).
- A question about migrating Billing, Radar or Connect.
- A doubt about where dunning and 3DS live.

## 3. Required data
The same set of payments on both sides (or, without Solidgate data, the documentation of both); `outcome.type` and `network_status` (Stripe) vs codes and anti-fraud decision (Solidgate); Radar rules vs Antifraud rules and lists; billing model and states; reserve and payout programs; the current topology.

## 4. Sources
- `../cross-provider/equivalence-matrix.md`
- Stripe: declines (https://docs.stripe.com/declines), 3D Secure (https://docs.stripe.com/payments/3d-secure), Radar rules (https://docs.stripe.com/radar/rules), disputes (https://docs.stripe.com/disputes), Billing and Smart Retries (https://docs.stripe.com/billing/revenue-recovery/smart-retries), webhooks (https://docs.stripe.com/webhooks), reports (https://docs.stripe.com/reports)
- Solidgate: `<cache>/solidgate/docs/risks/fraud/antifraud.md`, `<cache>/solidgate/docs/payments/payments-insights/error-codes.md`, `<cache>/solidgate/docs/billing/recover-revenue/smart-retries.md`, `<cache>/solidgate/docs/finance/financial-reports/settlements.md` (Stripe as a settlement provider), `<cache>/solidgate/docs/payments/integrate/webhooks.md`

## 5. Tools
`solidgate-payment-performance` (Solidgate lead), `solidgate-3ds-risk`, `solidgate-billing`, `solidgate-chargebacks`, `solidgate-reconciliation`; `stripe-payments`, `stripe-risk`, `stripe-disputes`, `stripe-billing`, `stripe-finance` (without a connected Stripe data source they act as methodology; with one, on real data). Economics is outside this base.

## 6. Procedure (read only)
1. Build the terms table by origin of decision: Stripe "failed" (issuer) vs "blocked" (Radar, `not_sent_to_network`) vs `invalid`; Solidgate issuer decline (3.xx), risk decline (4.xx) and routing decline (0.04). Mark codes 4.05, 4.07 and 4.09 as NEEDS REVIEW.
2. Compare risk: Radar (model, Stripe managed rules, account rules, risk controls) vs Antifraud (lists, rules, decisions Pass, Reject, Force 3DS, Review, shadow mode, Solidgate managed rules). A preview is not impact.
3. Compare 3DS: Stripe starts it and the issuer decides (3DS cannot be switched off by API) vs Solidgate with several deciders and `force3ds`; liability shift is documented for Stripe, and for Solidgate only what the pages read say (loss conditions NOT VERIFIED).
4. Compare dunning: Smart Retries (Stripe, a defined set of hard declines, configurable window, same PaymentIntent) vs the merchant retry, Billing smart retries, redemption and discounted retries (Solidgate); declare the grain.
5. Compare billing: object models, delinquency states, events; Stripe Connect payouts to partners have no verified equivalent in the Solidgate documentation read: NOT VERIFIED, ask the vendor.
6. Compare disputes and card scheme programs: windows and formulas differ (a rolling window on one side, an aggregate or cohort fraud rate on the other).
7. Compare webhooks (signature, retry, ordering) and reporting (Sigma and Reports vs v1 and v2 reports, financial entries, settlements).
8. If Stripe sits behind Solidgate, list what Solidgate sees and what Stripe sees (duplicated risk and 3DS) and what the settlement consolidates.
9. Write the nine-section answer, with a section per family.

## 7. Decision criteria
- No sentence "is equivalent to" without a source on both sides; otherwise "NOT VERIFIED".
- A critical conclusion (fraud, chargeback, 3DS, Radar, payouts, reserve, refund) is never reached by a skill alone: validate source, period, denominator, scope, account and conflicts with earlier data.
- A structural dependency (for example partner payouts that exist only on Stripe) weighs before any cost comparison.

## 8. Hypotheses
- H1 A Radar block and an Antifraud Reject are functionally similar but not identical. Validate with a real example on each side.
- H2 Part of the approval difference comes from who decides 3DS. Validate by flow.
- H3 Dunning is duplicated (Stripe Billing and Solidgate Billing) if both are active. Validate the owner.
- H4 Different dispute windows explain different ratios. Validate the formula.

## 9. Expected evidence
A terms table by origin with sources on both sides; paired real examples (when available); a gap matrix; a list of structural dependencies.

## 10. Recommendations
Proposals to the decision owner: keep the Stripe skills as methodology and checklist even on Solidgate topics; any migration of Billing, Radar or Connect needs its own analysis and approval; do not apply an equivalent Radar rule on Solidgate without a shadow mode preview. No execution.

## 11. Impacts and risks
Loss of partner payout capability; the risk of two risk systems in sequence; the risk of accounts with an inherited block; reserve and card scheme monitoring risk per acquirer.

## 12. Suggested tests
A backtest of the terms map on a hand-labeled sample; in the Solidgate sandbox, test cards for issuer and risk declines; a check of the settlement provider list (Stripe as a provider and its availability date) as documentation reading only.

## 13. Completion criteria
The terms table by origin is complete; gaps (Connect, liability shift conditions, risk model) declared; no equivalence assumed by name; closing sections "SOLIDGATE SQUAD APPLIED" and "STRIPE SKILLS APPLIED" present.
