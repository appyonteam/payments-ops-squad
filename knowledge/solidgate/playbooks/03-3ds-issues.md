> Status: draft. Not yet validated against a live Solidgate account.

# 03. 3DS issues

Common rules: see `README.md`. Main scenario: **B** (the customer authenticates and the payment is not approved). Supports **A**.

## 1. Objective
When 3DS completes and the transaction is still not approved, distinguish (a) a technical defect (the authentication result did not reach authorization, or arrived invalid), (b) an issuer decision (the data arrived and the issuer declined) and (c) a policy decision (who forced or waived 3DS), identifying the effective 3DS decider on each payment.

## 2. Symptoms
- Orders that pass `3ds_verify` and end in `auth_failed`.
- Challenge conversion falls; frictionless share is low.
- Growth in 2.15 (SCA requires authentication) on traffic without 3DS.
- Divergence between `three_ds.flow`, `eci` and the authorization result.

## 3. Required data
Per order: `three_ds.flow` (frictionless, challenge, none, unspecified; null means 3DS not started), `exception` (low_value, transaction_risk_assessment), `eci`, order status, error code, brand, BIN country, amount, `force3ds` sent, use of `external_mpi_data`, routing log decision (3DS decision, step skipped for 3DS), anti-fraud decision (Force 3DS), connector.

## 4. Sources
- `<cache>/solidgate/docs/payments/card-payments/3ds-verification.md` (flows and exceptions; external MPI)
- `<cache>/solidgate/docs/orchestration/routing-overview.md` (Force 3DS preset and evaluation order; 3DS cascade; soft decline and TRA-to-3DS fallbacks)
- `<cache>/solidgate/docs/orchestration/track-routing/trace-routing-decisions.md` (3DS decision and skip reasons)
- `<cache>/solidgate/docs/risks/fraud/antifraud.md` (Force 3DS decision)
- `<cache>/solidgate/docs/payments/card-payments/card-payments-insights/eci.md` and `verification-result.md` (indexed, not read in the original review: NOT VERIFIED until read)
- `<cache>/solidgate/docs/payments/digital-wallets/google-pay/google-pay-and-3ds.md`
- Other providers: Stripe 3D Secure and SCA documentation (https://docs.stripe.com/payments/3d-secure, https://docs.stripe.com/strong-customer-authentication), Primer 3D Secure overview (https://primer.io/docs/payment-services/3d-secure/overview), FunnelFox adaptive 3DS page (https://funnelfox.com/docs)

## 5. Tools
`solidgate-3ds-risk` (lead), `solidgate-routing` (presets and 3DS cascade), `solidgate-api-architect` (parameters such as `external_mpi_data`, `user_agent`, `time_zone_offset`), `solidgate-payment-performance`; `primer-3ds` and `funnelfox-3ds` for the user's current stack; `stripe-risk` and `stripe-payments` as methodology.

## 6. Procedure (read only)
1. Identify the effective 3DS decider per order: external MPI, MIT or MOTO exception, anti-fraud, API `force3ds` flag, Maestro rule, low value, SCA, or fallback after a soft decline. The evaluation order is in `routing-overview.md`; confirm in the routing log (3DS decision).
2. Confirm the result reached authorization: `eci`, `three_ds.flow` and, with an external MPI, `authentication_response` Y or A, a UUID `ds_transaction_id` and a `three_ds_version` of 2.x.
3. Read the final error code: an `eci` of successful authentication plus a format or integration error points to a technical defect; a valid `eci` plus an issuer decline (family 3.xx) points to an issuer decision.
4. Separate frictionless from challenge and measure challenge completion by brand, with a control.
5. Check whether the step's connector supports 3DS cascade before attributing loss to a "second authentication".
6. Treat the "with 3DS" group as an already-declined population when the flow is a soft decline fallback (structural bias); never compare "with" vs "without" 3DS as a causal effect.
7. Write the nine-section answer.

## 7. Decision criteria
- Technical defect: authentication data missing or invalid at authorization, or an MPI field rejected; action in integration (playbook 07).
- Issuer decision: complete data and a 3.xx decline; action on traffic quality, not on integration.
- Policy decision: Force 3DS by preset, flag or anti-fraud without proven need; action is a rule review, by human decision.
- Two deciders on the same payment: treat as a finding and escalate.

## 8. Hypotheses
- H1 `eci` or cryptogram not propagated (external MPI incorrectly filled). Validate: `external_mpi_data` rejections.
- H2 An exemption (low_value, TRA) was approved and the issuer declined later. Validate `exception`. Without authenticated 3DS there is no liability shift (documented for Stripe; for Solidgate: NOT VERIFIED).
- H3 Fallback did not reuse the authentication and produced a second challenge. Validate the "3DS Cascading: Supported" label of the connector.
- H4 A specific brand (for example Maestro or Mastercard) with a 3DS server failure. Validate against a control brand.
- H5 Insufficient browser data broke frictionless. Validate `user_agent` and `time_zone_offset`.

## 9. Expected evidence
A table flow x brand x result; a sample of orders with the routing log 3DS decision; a distribution of `eci` by result; before and after in the same time-of-day band with a control brand.

## 10. Recommendations
Proposals for review: fix how `external_mpi_data` is passed; review the Force 3DS preset or an anti-fraud rule; enable only connectors with 3DS cascade when the loss comes from a second challenge. Nothing is executed; a 3DS change is a write action needing named authorization.

## 11. Impacts and risks
Conversion (challenge costs conversion), chargeback (liability shift), the risk of two 3DS deciders on one route, regulatory SCA and PSD2 risk on European traffic (2.15).

## 12. Suggested tests
3DS test cards in the sandbox (`<cache>/solidgate/docs/payments/testing/card-payments.md`): frictionless, challenge, authentication failure and an external MPI with an invalid `authentication_response` (it should be rejected); validation by brand with a control.

## 13. Completion criteria
Decider identified by sample; classification defect vs issuer vs policy with evidence; the `eci.md` and `verification-result.md` pages read or the gap declared; no "with vs without 3DS" comparison presented as an effect.
