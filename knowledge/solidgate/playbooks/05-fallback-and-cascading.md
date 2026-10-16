> Status: reviewed against the official documentation (2026-10-09). Not validated against a live account.

# 05. Fallback and cascading

Common rules: see `README.md`. Supports scenarios **A**, **B**, **C** and **D**.

## 1. Objective
Understand and measure what each mechanism called "fallback", "cascade" or "route retry" does on Solidgate and how it differs from Primer, FunnelFox and Stripe, so that recovery by route change is evaluated without comparing things that are not comparable. If a fallback, retry or 3DS question names no processor, first map the user's current stack (for example FunnelFox → Primer → Stripe) and decide which layer owns each rule.

## 2. Symptoms
- Payments approved on the 2nd or 3rd step with the decline code of the 1st; or declined on every step.
- A repeated 3DS challenge in the same purchase.
- More blocks on the destination account of a cascade.
- A fallback recovery rate that does not reconcile with the total gain.

## 3. Required data
Per order: sequence of steps tried, connector and account of each step, decline code per step, stop reason (stop error code), fallback applied (soft decline, TRA-to-3DS, retry with the initial connector, card or card-on-file), whether 3DS was reused, final result; the entry population (rule and origin account) and the regime in force before and after a publication.

## 4. Sources
- `<cache>/solidgate/docs/orchestration/routing-overview.md` (cascade with up to five steps; stop error codes; fallbacks and their effect on the cascade)
- `<cache>/solidgate/docs/orchestration/track-routing/trace-routing-decisions.md`
- `<cache>/solidgate/docs/payments/card-payments/recover-revenue/retrying-declined-charges.md`
- Comparison: Primer fallbacks (https://primer.io/docs/payment-services/fallbacks), FunnelFox payment cascading and retries (https://funnelfox.com/docs), Stripe 3DS and SCA documentation (https://docs.stripe.com/strong-customer-authentication)

## 5. Tools
`solidgate-routing` (lead), `solidgate-3ds-risk`, `solidgate-payment-performance`; `primer-workflows`, `funnelfox-orchestration` and `funnelfox-retries` for fallbacks in the user's current stack; `stripe-payments` and `stripe-risk` (effect of blocking on the destination account).

## 6. Procedure (read only)
1. For the configuration under analysis, list the fallbacks per step (all disabled by default) and their order of application (soft decline fallback, TRA-to-3DS fallback, retry with initial connector, card or card-on-file fallback); record which ones stop the cascade and which let it continue.
2. Distinguish a fallback (same connector account, modified request) from a cascade (another step) in the data: use the routing log and the step sequence, not the `declineReasons` of an approved payment.
3. Read the effect by the entry population (the rule that matched) and identify a fallback by a final connector different from the one the current rule predicts; never by "approved with a recorded decline" (which includes recovery by 3DS on the same account).
4. Check whether 3DS was reused on the next step (the "3DS Cascading: Supported" label on the step or connector); if not, count the second challenge as friction.
5. Check the stop error code that ended the cascade; invalid card or token codes are not solved by another route.
6. Measure the destination account: blocks and declines inherited from the origin route; the combined conversion of the accounts.
7. Record the prior regime (no fallback) as a baseline, in the same time-of-day band and with a control.
8. Write the nine-section answer.

## 7. Decision criteria
- Keep or extend a cascade only if combined conversion (origin plus destination) improves against the prior regime, with a control.
- A cascade that generates blocks on a destination account or a second challenge without net gain is a candidate for review (by human decision).
- Recovery is attributed to a fallback only if the final connector differs from the one the rule predicts.
- Without prior regime data, the result is "observed recovery", not "gain".

## 8. Hypotheses
- H1 Part of the "fallback recovery" is 3DS on the same connector (soft decline fallback). Validate by final connector.
- H2 3DS is not reused and the customer authenticates twice. Validate the connector support.
- H3 The destination account inherits risk from the origin. Validate by block rate per entry.
- H4 A stop error code spares a useless attempt. Validate the share of payments stopped by stop codes.

## 9. Expected evidence
A table entry x final step x result; combined conversion before and after; count of second challenges; distribution of stop reasons; a sample of routing logs.

## 10. Recommendations
Proposals: enable fallback per step in a controlled test, prefer 3DS cascading where supported, define additional stop codes to evaluate with Solidgate support. Execution is outside the playbook; any routing version publication needs named approval and a rollback plan.

## 11. Impacts and risks
Response latency from extra steps; processing cost per extra attempt; risk of blocks on the destination; risk of duplicating a fallback that already exists in Primer or FunnelFox (orphan authorization, multiplied attempts); card scheme monitoring risk from extra attempts.

## 12. Suggested tests
Sandbox with test cards that force a decline on the 1st step; verify that the configured fallback is the only one applied per attempt; a publication test with a payment in flight in a test environment (effect NOT VERIFIED in the documentation read).

## 13. Completion criteria
Every mechanism described with name, effect on the cascade and source; entry-based reading done; combined conversion reported; gaps (effect on in-flight payments, connector rules) declared.
