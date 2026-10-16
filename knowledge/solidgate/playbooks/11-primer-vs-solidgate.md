> Status: reviewed against the official documentation (2026-10-09). Not validated against a live account.

# 11. Primer vs Solidgate

Common rules: see `README.md`. Main scenario: **E** (Primer and Solidgate report different approval rates). A mixed topic: involve the Solidgate and Primer specialists, with closing sections "SOLIDGATE SQUAD APPLIED" and "PRIMER SQUAD APPLIED", plus the Stripe skills as methodology if Stripe sits behind Primer.

## 1. Objective
Explain why Primer and Solidgate show different approval rates, or why a switch or coexistence would give a different result, separating a difference of definition (grain, denominator, window), of mix, of architecture (who decides 3DS, routing and retry) and of real performance.

## 2. Symptoms
- The Primer dashboard and the Solidgate dashboard show different rates for the "same" period.
- One platform recovers more than the other and nobody knows why.
- A comparison by brand or country that is contradictory between the two.
- A doubt whether Solidgate replaces Primer or sits behind or beside it.

## 3. Required data
From both platforms, for the same set of payments: a common identifier, the first transaction per payment, mix (BIN country, brand, type, amount, CIT vs MIT), 3DS (who decided), route and final processor, raw codes, retries per layer. Without Solidgate data for the user's own traffic, the comparison is documentary (architecture and definitions), never about performance.

## 4. Sources
- `../cross-provider/equivalence-matrix.md` (all domains; divergences section)
- Primer: authorization rate, Workflows and fallbacks, declines, webhooks and reconciliation (https://primer.io/docs/concepts/payment-lifecycle, https://primer.io/docs/workflows/overview, https://primer.io/docs/payment-services/fallbacks, https://primer.io/docs/reconciliation/unified-settlement-report)
- Solidgate: `<cache>/solidgate/docs/payments/payments-insights/payment-analytics.md`, `<cache>/solidgate/docs/orchestration/routing-overview.md`, `<cache>/solidgate/docs/payments/card-payments/3ds-verification.md`

## 5. Tools
`solidgate-payment-performance` (Solidgate lead), `solidgate-routing`, `solidgate-3ds-risk`; `primer-squad` (decides which Primer specialists join), `primer-performance`, `primer-workflows`, `primer-3ds`, `primer-payments`; `stripe-payments` and `stripe-risk` (the processor behind Primer, if any). Confirm vendor documentation with a date before relying on it.

## 6. Procedure (read only)
1. Align definitions before comparing. For Primer, check in your own dashboard and data how the authorization rate is defined and whether it counts payments or attempts; internal attempts (fallback, adaptive 3DS inside one payment) may count only through the final status, and a dunning retry may count as a new payment. For Solidgate: approved orders divided by total orders. Declare grain, denominator, window and time zone on each side; if they do not align, the figures are not comparable.
2. Recompute, on both sides, the approval of the first transaction over all payments, with the same window and mix.
3. Map who decides each thing on both sides: 3DS (one decider per route in some Primer setups; several internal deciders on Solidgate), routing (Workflows vs routing configuration), fallback (a workflow with a second authorization vs step-level fallback and cascade), retry and tokenization.
4. Compare codes by origin (block vs issuer vs technical), never by name; read the raw code when an orchestrator labels a decline generically.
5. If overlap is possible (Solidgate behind or beside Primer), identify the decider of each layer and the risk of a duplicated decision.
6. Read the effect of a fallback by entry and identify it by the final processor.
7. Separate the difference attributable to definition, mix, architecture and performance; what remains is "performance not determined".
8. Write the nine-section answer, with a section per specialist family.

## 7. Decision criteria
- No performance conclusion without aligned definitions, controlled mix and equal window.
- If grain or denominator cannot be aligned, report "not comparable" and stop.
- An architecture with two deciders for the same payment is a risk finding, not a gain.
- Any recommendation to switch or coexist needs an official simulation and a migration cost (vault, descriptor, partners, dual operation), outside this playbook.

## 8. Hypotheses
- H1 The difference is definition (per payment vs per order, with or without retries). Validate by recomputation.
- H2 The difference is mix (country, brand, CIT vs MIT). Validate with a fixed mix.
- H3 One platform attributes to the other what is really a processor block. Validate by the raw code.
- H4 Different 3DS deciders produce different frictionless and challenge shares. Validate by flow.
- H5 Cascade and fallback have different mechanics and count recovery differently. Validate by entry. A Primer fallback is a second authorization within the same payment; whether each Solidgate cascade step counts as a transaction or an order is NOT VERIFIED.

## 9. Expected evidence
A side by side definitions table (grain, denominator, window, time zone, retry treatment); first transaction approval by segment on both sides; a decider map per layer; a paired sample per payment (when data exists on both sides).

## 10. Recommendations
Proposals for the decision owner: adopt a single approval definition for any comparison; evaluate replacement or coexistence only after an official simulation and a decider map; run a controlled pilot on a small slice, by human decision.

## 11. Impacts and risks
A high-impact architecture decision (replacing an orchestrator); the risk of comparing figures of different grains; the risk of two deciders; migration and dual operation costs outside this base; regulatory and card scheme risk when changing route.

## 12. Suggested tests
Cross recomputation: apply the Solidgate definition to Primer data and the Primer definition to Solidgate data (where available); a paired sample of 30 payments checked line by line; a sanity test that the segments add up to the total.

## 13. Completion criteria
Definitions aligned or the comparison declared not comparable; the difference decomposed into definition, mix, architecture and performance; a decider map delivered; no invented number in the recommendation.
