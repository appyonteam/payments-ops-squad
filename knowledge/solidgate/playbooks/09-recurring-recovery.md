> Status: reviewed against the official documentation (2026-10-09). Not validated against a live account.

# 09. Recurring revenue recovery

Common rules: see `README.md`. Main scenario: **D** (recover recurring revenue). Supports **A** (renewals) and **B**.

## 1. Objective
Evaluate, with grain and denominator declared, how Solidgate recovers failed recurring charges (merchant retry with token, Billing smart retries and strategies, redemption, discounted retries, routing cascade) and how that compares with the user's current stack (for example a funnel tool's retry logic, Primer, Stripe Smart Retries). When Solidgate acts as the processor behind a funnel tool, Solidgate owns dunning and the funnel tool's own retry logic does not apply; two owners exist only during a migration or on mixed routes. Do this before any promise of gain.

## 2. Symptoms
- Declined renewals with a code pattern (funds, issuer, general); involuntary churn.
- Subscriptions stuck in REDEMPTION or UNPAID.
- Retries in several layers on the same card; more blocks as the attempt number grows.
- A per-charge rate falling while approved count and revenue rise (mixed grain).

## 3. Required data
Per subscription cycle: attempt number, decline code, MAC, interval between attempts, the layer that tried (Solidgate Billing, merchant, funnel tool, Stripe Billing), discount applied in a discounted retry, result, subscription state (REDEMPTION, UNPAID, CANCELLED, ACTIVE) and invoice state (DUNNING, PAID, UNPAID, VOIDED), Billing version (1.0 or 2.0), `retry_mode`, cards by brand; the eligible population quantified.

## 4. Sources
- `<cache>/solidgate/docs/billing/recover-revenue/overview.md` (redemption), `smart-retries.md` (default retry pattern and ceiling; discounted retries; `retry_mode`), `retry-strategies.md` (weekly strategies)
- `<cache>/solidgate/docs/billing/subscriptions/subscriptions-2.0/billing-events.md` (access by status)
- `<cache>/solidgate/docs/payments/card-payments/recover-revenue/retrying-declined-charges.md` and `merchant-advice-codes.md`
- `<cache>/solidgate/docs/payments/payments-insights/error-codes.md` (network limits)
- Comparison: Stripe Smart Retries (https://docs.stripe.com/billing/revenue-recovery/smart-retries), FunnelFox payment retries and billing settings (https://funnelfox.com/docs), Primer documentation (https://primer.io/docs)

## 5. Tools
`solidgate-billing` (lead), `solidgate-payment-performance`, `solidgate-routing` (cascade on MIT), `solidgate-incident-investigator`; `funnelfox-retries`, `funnelfox-billing` and `primer-payments` for the user's current stack; `stripe-billing`, `stripe-payments` as methodology. The user decides who owns dunning; the agents do not.

## 6. Procedure (read only)
1. Declare the retrying layer and the unit. Some orchestrators count each dunning retry as a new payment; Stripe Billing keeps retries on the same PaymentIntent; Solidgate Billing reuses or reissues the invoice depending on the version. Check how the user's stack counts it. Fix the grain (subscription cycle) and the denominator.
2. Count the base by state (REDEMPTION, UNPAID, CANCELLED) as an honest denominator before discussing gain.
3. Classify failures by code and MAC: retryable (funds, general, issuer), customer (card, data), technical, do not retry. Separate risk blocks from issuer declines.
4. Measure recovery by attempt number and by code; an attempt with zero recovery is a cost.
5. Check the sum of attempts across layers per card against network limits (which diverge between pages: NEEDS REVIEW).
6. Evaluate the access rule during the retry window (a merchant decision; Solidgate imposes no time) and whether the redemption window is included in the next period.
7. Verify discounted retries: only after 3.02, 30 minutes later, and they count toward the ceiling; cost equals the discount granted.
8. Isolate the retryable and addressable population from the proven recoverable one (only the latter has uplift against a control).
9. Write the nine-section answer.

## 7. Decision criteria
- One dunning owner per route: never two layers retrying the same card without coordination.
- Cut attempts only if recovery per attempt is nil and revenue does not fall; otherwise the metric improves and the business does not.
- A discounted retry only if the revenue lost to the discount is below the revenue recovered, in a controlled test.
- Expected gain: "NOT YET MEASURABLE" until a control exists.

## 8. Hypotheses
- H1 Recovery concentrates in a few early attempts. Validate by attempt.
- H2 Retrying in two layers manufactures blocks. Validate risk by attempt.
- H3 A relevant share of failures are technical errors or invalid cards (not recoverable). Validate by class.
- H4 Including or excluding the redemption window in the period changes apparent revenue. Validate by renewal date.
- H5 A missing `next_charge_at` in a webhook leaves the consumer in a wrong state. Validate with a status query a few seconds later.

## 9. Expected evidence
A recovery curve by attempt and by code; a distribution by state; attempts per card summed across layers; a controlled test (when data exists); a list of field gaps.

## 10. Recommendations
Proposals: choose the dunning owner, set a global per-card attempt limit, evaluate the Solidgate strategy against the funnel tool's retry logic in a controlled pilot, define the access policy during the window. This playbook changes no configuration; changing `retry_mode`, strategy or discount is a write action (named approval).

## 11. Impacts and risks
Recurring revenue and involuntary churn; a card scheme fee risk from excess attempts; the risk of duplicated retries; a misleading metric; the risk of improper access during redemption.

## 12. Suggested tests
Sandbox: a short-period subscription with the recurring decline test card to observe `INVOICE_PAYMENT_FAILED`, `SUBSCRIPTION_REDEMPTION_STARTED` and `SUBSCRIPTION_UNPAID`; a pilot with a control (with and without) for any strategy; a backtest of the class map on labeled historical failures.

## 13. Completion criteria
Dunning owner defined or the open question recorded; recovery measured by attempt with grain declared; retryable, addressable and recoverable populations separated; diverging network limits flagged; no promise of gain without a control.
