> Status: draft. Not yet validated against a live Solidgate account.

# 01. Low approval rate

Common rules (read only, v1 is not v2, no fabrication): see `README.md`. Scenario covered: **A** (approval falls sharply; any rates are illustrative, not measurements).

## 1. Objective
Break a drop or a persistently low approval rate into causes by layer, using the chain: approval loss, decline, 3DS, processor, routing, retry, cascading, tokenization, issuer. Deliver a diagnosis with grain, denominator and window declared, without promising a gain.

## 2. Symptoms
- Payment analytics approval rate drops or sits below what the mix would predict.
- Platform-side blocks (0.04 routing, 4.05, 4.07, 4.09) grow relative to issuer declines (family 3.xx).
- Orders stuck in `3ds_verify` that never reach `auth_ok` (see playbook 03).
- A change in mix (country, brand, BIN, CIT vs MIT, amount) or in the routing configuration version (see playbook 04).

## 3. Required data
1. Order and transaction extract for the period, with `payment_type`, `three_ds.flow`, `eci`, error code, brand, BIN or country, connector and connector account, routing configuration version. Source: the card orders report (v1) or an export the user provides. Without it the playbook stops at "Gaps".
2. A comparable baseline (same time-of-day band, same mix) and a control group (a brand or segment not affected).
3. A change timeline: published routing versions, anti-fraud rule changes, checkout changes.
4. The definition of "approval" used by each dashboard (grain and denominator).

## 4. Sources
- `<cache>/solidgate/docs/payments/payments-insights/payment-analytics.md` (approval rate is approved orders divided by total orders; approval volume vs gross volume)
- `<cache>/solidgate/docs/payments/payments-insights/error-codes.md` (action categories: Retry, Customer action, Developer action, Contact support, Do not retry)
- `<cache>/solidgate/docs/payments/card-payments/card-payments-insights/payment-lifecycle.md` (statuses, `payment_type`)
- `<cache>/solidgate/docs/orchestration/track-routing/trace-routing-decisions.md` and `monitor-routing-analytics.md`
- `<cache>/solidgate/docs/reporting/operational-reports/card-orders.md`
- `../cross-provider/equivalence-matrix.md` (payment lifecycle and risk domains)

## 5. Tools
`solidgate-payment-performance` (lead), `solidgate-routing`, `solidgate-3ds-risk`, `solidgate-incident-investigator` (if there is an incident); `primer-performance` and `funnelfox-performance` for the user's current stack (for example FunnelFox → Primer → Stripe); `stripe-payments` and `stripe-risk` as methodology. No live API call without credentials and explicit approval; any mocked tooling is not evidence.

## 6. Procedure (read only)
1. Declare grain, denominator, window, time zone and source of every number (order, transaction or attempt) before any calculation.
2. Confirm the drop in raw data, not on the dashboard: recompute the approval of the first transaction over all orders (empty or null `payment_type` on the first) and separate CIT from MIT and retries.
3. Control the mix: repeat by BIN country, brand, card type, amount, channel and method (card vs wallet).
4. Classify declines by origin: platform block (0.04, 4.05, 4.07, 4.09), issuer (3.xx), merchant technical error (Developer action), 3DS (2.15 and `3ds_verify`).
5. Cross with the change timeline and the active routing version; read the routing log of affected orders (selected step, skipped steps, payment blocked, 3DS decision).
6. For any known mid-period change, compare the same time-of-day band against a control brand.
7. Separate the effect by layer and record what could not be separated.
8. Write the nine-section answer with confidence and gaps.

## 7. Decision criteria
- The drop is confirmed only if it persists after mix and window controls; otherwise it is a composition change.
- Cause "block" if the share of 0.04, 4.05, 4.07 and 4.09 grew without a proportional growth in issuer declines.
- Cause "3DS" if the loss concentrates in `3ds_verify` or in authentication declines.
- Cause "routing" if it coincides with a version publication or a connector account change.
- Without a control, the result is a "signal", not a "cause".

## 8. Hypotheses (each with its validation)
- H1 Mix change explains the drop. Validate: rate by segment with fixed mix.
- H2 An anti-fraud or routing block grew. Validate: counts by code and rule hits (shadow mode).
- H3 A 3DS defect (result did not reach authorization). Validate: `eci`, `three_ds.flow` and error code (playbook 03).
- H4 A new routing version or a new connector account performs worse. Validate: filter by configuration version and route.
- H5 A merchant technical error (invalid field, IP, parameter). Validate: "Developer action" codes.
- H6 Retries inflated the denominator or were counted as new payments. Validate: `payment_type: retry` and grain.

## 9. Expected evidence
A table per segment with n, numerator, denominator, period and source; a distribution of codes by origin; a sampled routing log; before and after in the same time-of-day band with a control. Insufficient evidence is declared as such.

## 10. Recommendations
Recommendations are proposals, never execution: fix the integration (if H3 or H5), review an anti-fraud rule in shadow mode (if H2), revert to a prior routing version (if H4, by human decision), adjust traffic mix. Each carries a hypothesis, a guardrail, a rollback and an exit metric. Expected impact only with a basis; otherwise "NOT YET MEASURABLE".

## 11. Impacts and risks
Revenue and chargeback impact (loosening a block can raise fraud); risk of comparing different grains; risk of blaming the orchestrator for an issuer decision; risk of concluding from a small sample. Compliance: mask personal data in extracts, no PAN or CVV.

## 12. Suggested tests
Retroactive validation (the decomposition lights up on a known incident, if one exists); a 30-order sample checked line by line against the routing log; a denominator sanity test (segments add up to the total); sandbox with Solidgate test cards for each decline code (`<cache>/solidgate/docs/payments/testing/card-payments.md`), never production.

## 13. Completion criteria
Main cause identified with evidence and control, or "cause not determined" with the list of missing data; grain and denominator declared; no number without a basis; recommendations with guardrail and rollback; closing line "SOLIDGATE SQUAD APPLIED" (local files used, API version, gaps).
