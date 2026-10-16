> Status: draft. Not yet validated against a live Solidgate account.

# 08. Chargebacks and disputes

Common rules: see `README.md`. Supports scenario **A** (when the drop comes from a risk block) and prevention decisions. This playbook executes no dispute response, refund or evidence upload.

## 1. Objective
Read and compare the Solidgate dispute lifecycle (1st_chb, 2nd_chb, arbitration; RDR, Order Insight, Consumer Clarity, CE3.0; representment) with Primer, FunnelFox and Stripe, and evaluate prevention and defense without assuming that "alert", "dispute" and "chargeback" are equivalent.

## 2. Symptoms
- Growth in chargebacks, fraud alerts or prevention alerts.
- Chargebacks close to their deadline; status `accepted` because of an expired deadline; `resolved` by RDR.
- A fraud or dispute ratio approaching a card scheme program threshold.
- A doubt between keeping automatic refunds (a funnel tool), alerts (Ethoca, RDR) or representment (Solidgate).

## 3. Required data
Disputes with `type`, `status`, `reason_group`, `reason_code`, `deadline_date`, `represented_by`, `arn_code`, amount and currency; alerts (fraud alerts v1 or v2, prevention alerts) with dates; sales per month and cohort; evidence available per reason (access, login, IP, device, billing notice 10 days before, cancellation policy); the current refund or alert regime in the user's stack.

## 4. Sources
- `<cache>/solidgate/docs/risks/chargebacks.md` (flow, types, statuses, tracking, automatic and manual representment, deadlines, when to accept or contest)
- `<cache>/solidgate/docs/risks/prevention-alerts/prevent.md` (Order Insight, Consumer Clarity, CE3.0) and `resolve.md` (RDR and Mastercom)
- `<cache>/solidgate/docs/risks/fraud/fraud-overview.md` (aggregate and cohort fraud rate)
- `<cache>/solidgate/docs/risks/reason-codes.md`, `monitoring-programs/visa.md`, `monitoring-programs/mastercard.md` (indexed, not read in the original review: NOT VERIFIED)
- `<cache>/solidgate/docs/reporting/operational-reports/chargebacks.md`
- Other providers: Stripe disputes (https://docs.stripe.com/disputes) and monitoring programs (https://docs.stripe.com/disputes/monitoring-programs), Primer disputes (https://primer.io/docs/disputes/overview), FunnelFox dispute alerts (https://funnelfox.com/docs)
- Vendor skill `solidgate-chargebacks-alerts` (v1 only, possibly outdated)

## 5. Tools
`solidgate-chargebacks` (lead), `solidgate-3ds-risk` (liability shift and anti-fraud), `solidgate-reconciliation` (financial impact); `primer-payments` and `funnelfox-payments` for the user's current stack; `stripe-disputes` and `stripe-risk` as methodology. Any "get dispute" step is a local read over an export.

## 6. Procedure (read only)
1. Inventory disputes by stage and status, and take the authoritative deadline from `deadline_date` (not the generic per-brand deadline table).
2. Classify by reason (group and code) and brand; separate fraud (for example Visa 10.4) from consumer disputes and from recurring cancellation.
3. Separate what was prevented (resolved, RDR, handled alert) from what became a chargeback; `resolved` does not affect the dispute ratio according to the documentation, but it is a lost sale and should appear separately.
4. Compute ratios (fraud and dispute) with a declared definition: aggregate (current month, settlement date, Visa and Mastercard) or cohort (up to 180 days); do not mix with the rolling window used by card scheme programs elsewhere in the stack.
5. For each eligible dispute, list available and missing evidence by reason (digital: login, IP, device; recurring: cancellation policy, 10 day notice, service usage). Weigh cost against recovery (thresholds cited by the documentation itself; pre-arbitration and arbitration are outside auto-representment).
6. Map what exists in the current stack (funnel tool dispute alerts with automatic refund; Stripe early fraud warnings and disputes) to avoid overlap or gaps.
7. Write the nine-section answer, with coverage, addressability and recoverability kept separate.

## 7. Decision criteria
- Contest: evidence that answers the reason, authenticated 3DS (shift possible), a first chargeback, an amount that justifies the cost.
- Accept: no evidence, a low amount, confirmed fraud, a refund already issued, pre-arbitration or arbitration cost above the amount.
- Prevention: only if the alert is actionable without duplicating a refund already automatic in another layer.
- "Eligible dispute" is never presented as expected recovery without a control.

## 8. Hypotheses
- H1 Part of the chargebacks have a cancelled-recurring reason. Validate by reason code and cancellation log.
- H2 Alerts (Ethoca, RDR) reduce formal chargebacks but not revenue loss. Validate by separating `resolved`.
- H3 Fraud concentrates in a segment or rule. Validate by cohort.
- H4 A deadline was missed for lack of a `deadline_date` monitor. Validate `accepted` without a defense.
- H5 The Solidgate ratio differs from the card scheme program ratio by window and denominator. Validate the formula.

## 9. Expected evidence
A table stage x status x reason x amount; ratios with formula and window; a queue by deadline; an evidence list by reason; an overlap map of prevention layers.

## 10. Recommendations
Proposals: a deadline monitor on `deadline_date`, a contest vs accept matrix, a prevention layer design without duplicate refunds, an evidence plan per reason. Enabling auto-representment, sending evidence or issuing a refund are write actions outside the playbook (named approval).

## 11. Impacts and risks
Revenue (loss from disputes and from prevention), arbitration cost, card scheme program risk, processor reserve risk, data protection risk when handling evidence with customer data (mask it), and re-onboarding of alerts per descriptor if traffic moves to another route.

## 12. Suggested tests
A backtest of the contest vs accept matrix on closed historical disputes (with authorized data); a deadline simulation with `deadline_date`; in the sandbox, the dispute webhook flow to validate the consumer (no production).

## 13. Completion criteria
Disputes classified with formula and window declared; a decision matrix with evidence per reason; overlap of layers mapped; monitoring program and reason code pages read or the gap declared; no write action executed.
