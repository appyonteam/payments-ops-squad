> Status: draft. Not yet validated against a live Solidgate account.

# 02. Decline codes

Common rules: see `README.md`. Supports scenarios **A**, **B**, **D** and **E**.

## 1. Objective
Read, classify and compare Solidgate decline codes without assuming equivalence with Primer, FunnelFox or Stripe codes, separating who decided (issuer, risk platform, routing, merchant integration) from what to do (retry, customer action, technical fix, support, do not retry).

## 2. Symptoms
- A code concentrates without explanation (for example 0.01 general, 3.02 insufficient funds, 3.04 issuer, 4.xx risk).
- Repeated retries with the same code; growth in "Developer action".
- The same card is approved on one processor and declined on another with a different code.
- The orchestrator label differs from the raw processor code.

## 3. Required data
Error code (format `N.NN`) per transaction with date, connector, connector account, `payment_type`, brand, BIN, amount; Merchant Advice Code when present; attempt order within the cascade; `three_ds.flow` and `eci`; the raw connector code if the order log carries it (NOT VERIFIED whether Solidgate exposes the raw acquirer code in reports).

## 4. Sources
- `<cache>/solidgate/docs/payments/payments-insights/error-codes.md` (action categories, network limits, asynchronous update of results)
- `<cache>/solidgate/docs/payments/card-payments/recover-revenue/retrying-declined-charges.md` (codes with a chance of success; codes not to retry)
- `<cache>/solidgate/docs/payments/card-payments/recover-revenue/merchant-advice-codes.md`
- `<cache>/solidgate/docs/orchestration/routing-overview.md` (stop error codes; decline 0.04)
- `<cache>/solidgate/docs/risks/fraud/antifraud.md` (code 4.09)
- `<cache>/solidgate/docs/payments/alternative-payments/apms-insights/error-codes.md` (alternative payment method codes, separate from cards)
- Other providers, for comparison by origin: Stripe declines documentation (https://docs.stripe.com/declines and https://docs.stripe.com/declines/codes), Primer declines and raw decline messages (https://primer.io/docs), FunnelFox hard decline mapping in billing settings (https://funnelfox.com/docs)

## 5. Tools
`solidgate-payment-performance` (lead), `solidgate-routing` (routing and cascade codes), `solidgate-3ds-risk` (2.15 and risk codes), `solidgate-api-architect` (integration errors); `primer-performance`, `funnelfox-retries` and `stripe-payments` for the user's current stack. Any "analyze declines" step is a local analysis over an export, declared as such.

## 6. Procedure (read only)
1. Extract the code distribution by count and by value, with n, period and grain. Never by count alone: a count-based rate can hide an incident.
2. Map each code to the Solidgate action category (Retry, Customer action, Developer action, Contact support, Do not retry) from `error-codes.md`; record codes the page does not classify as NOT VERIFIED.
3. Separate origin: platform (0.04 routing, 4.05, 4.07, 4.09), issuer (family 3.xx), integration (Developer action), authentication (2.15), token (5.02, 7.01).
4. Cross with the Merchant Advice Code when present (`isRetry`, the interval guidance) before deciding to retry.
5. Compare providers by origin, not by name: Solidgate 4.09 and Stripe `highest_risk_level` are blocks; an orchestrator's generic decline label can mask a block.
6. In a cascade, verify which step produced the code you see (entry vs final).
7. Write the nine-section answer; list as NEEDS REVIEW codes whose description diverges between pages (4.05, 4.07, 4.09).

## 7. Decision criteria
- "Retry" only for a code classified as retryable, within the per-card attempt limit and without an MAC that forbids it.
- "Do not retry" or a stop code ends the attempt and changes the flow (another payment method, update the card).
- A platform-origin code is not treated with retry; it is treated with rules, signals and a conversation with the processor.
- A Developer action code goes to integration fixes (playbook 07), outside the soft decline denominator.

## 8. Hypotheses
- H1 A general code (0.01) hides a mix of causes. Validate with the MAC and the raw code, if available.
- H2 A 3.xx decline concentrated in one brand or BIN is an issuer decision. Validate by BIN.
- H3 4.0x concentrated in a period coincides with a rule change. Validate against the rule history.
- H4 A different code across processors for the same card comes from taxonomy, not from a different decision. Validate with the raw code on each side.

## 9. Expected evidence
A table code x origin x category x n x value; a cross with MAC; a sample of transactions with cascade. For cross-provider comparison, a "same card, same window" table with both raw codes.

## 10. Recommendations
A proposed code-to-action map (for human review); an equivalent hard decline mapping to evaluate, never copied; exclusion of Developer action from the denominator; raw code instrumentation if missing. No execution.

## 11. Impacts and risks
Retrying on the wrong code adds cost, blocks and a risk of card scheme fees (attempt limits diverge between pages: NEEDS REVIEW). Classifying a block as an issuer decline leads to the wrong action.

## 12. Suggested tests
Solidgate sandbox test cards to provoke each category (`<cache>/solidgate/docs/payments/testing/card-payments.md`); the documentation warns that the code appears only in asynchronous updates; compare the proposed map against a hand-labeled sample.

## 13. Completion criteria
Every code seen has an origin, a category and an action, or is marked NOT VERIFIED; divergences documented; no equivalence assumed by name; no number without a basis.
