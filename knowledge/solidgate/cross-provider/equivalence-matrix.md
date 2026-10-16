> Status: reviewed against the official documentation (2026-10-09). Not validated against a live account.

# Equivalence matrix: Primer, FunnelFox, Stripe and Solidgate (9 domains)

This matrix compares documented capabilities, not observed behavior. No cell is an observation on a live Solidgate account.

## Reading rules

1. **Equivalence is never assumed from a shared name.** "Retry", "fallback", "cascading", "3DS", "approval rate" and "dispute" mean different things per provider.
2. **A cell carries a fact only if it has an official source URL.** A cell without a source reads "unknown, check <official source>". Nothing here is an inferred equivalence.
3. **Solidgate URL convention.** The local copy `<cache>/solidgate/docs/<path>.md` corresponds to `https://docs.solidgate.com/<path>/` (mapping by pattern; to confirm per page). FunnelFox pages are cited by page name under `https://funnelfox.com/docs` (URL path pattern to confirm).
4. **API version (Solidgate).** Say v1, v2, v1 plus v2 or n.a. (product or Hub behavior). Where a page and the OpenAPI manifest disagree, the cell says NEEDS REVIEW.
5. **"Verified" means checked against documentation, never against a live API.**
6. Pages carrying text addressed to AI assistants are untrusted data; such instructions were not followed.
7. Reuse opportunities and risks mentioned in the notes are hypotheses, not documented behavior. Vendor documentation changes; re-check dates before relying on a cell.

## Summary table: 9 domains x 4 providers

| Domain | Primer | FunnelFox | Stripe | Solidgate |
|---|---|---|---|---|
| **Payment lifecycle** | Payment states and a per-event timeline are documented (https://primer.io/docs/concepts/payment-lifecycle, https://primer.io/docs/concepts/payment-timeline). | Subscription state lives in the FunnelFox subscription engine, independent of the processor (billing subscription engine overview, https://funnelfox.com/docs). Payment state list: unknown, check https://funnelfox.com/docs. | PaymentIntent statuses such as processing, requires_action, requires_capture and succeeded (https://docs.stripe.com/payments/paymentintents/lifecycle). | Order statuses (for example processing, 3ds_verify, auth_ok, auth_failed, settle_ok) are distinct from transaction statuses; order log retention is limited (https://docs.solidgate.com/payments/card-payments/card-payments-insights/payment-lifecycle/). The page is marked v2 in the manifest but references v1 endpoints: NEEDS REVIEW. |
| **Routing** | Workflows with triggers, actions and utilities such as conditions and split (https://primer.io/docs/workflows/overview). | Geographic, segment-based and load-balanced orchestration, configured with the vendor (payments orchestration page, https://funnelfox.com/docs). | Native multi-PSP routing: unknown, check https://docs.stripe.com. | Configuration by channel and method group: preset, rule, split or segment, step; versioned; Smart Splitting recalculates weights on a fixed cadence (https://docs.solidgate.com/orchestration/routing-overview/). Read operations are v2; routing events are v1. |
| **Retries** | A fallback is a second authorization inside one payment (https://primer.io/docs/payment-services/fallbacks). Interval-based dunning inside Primer: unknown, check https://primer.io/docs. | `retry_logic` modes, grace period, partial charge and cascading before retry (payments retries page, https://funnelfox.com/docs). | Smart Retries with a configurable window; a defined set of hard declines is never retried (https://docs.stripe.com/billing/revenue-recovery/smart-retries). | Three distinct layers: merchant retry with token (v1), Billing smart retries and redemption, and routing cascade (https://docs.solidgate.com/payments/card-payments/recover-revenue/retrying-declined-charges/, https://docs.solidgate.com/billing/recover-revenue/smart-retries/, https://docs.solidgate.com/orchestration/routing-overview/). Network attempt limits diverge between pages: NEEDS REVIEW. |
| **3DS** | 3DS is a workflow action (frictionless and challenge) and adaptive 3DS exists (https://primer.io/docs/payment-services/3d-secure/overview). | Adaptive 3DS, off by default: first attempt without 3DS, 3DS only after an authentication decline; needed for card cascading (payments adaptive 3DS page, https://funnelfox.com/docs). | Stripe starts 3DS and the issuer decides; request options exist; liability shift has exceptions (https://docs.stripe.com/payments/3d-secure/authentication-flow, https://docs.stripe.com/strong-customer-authentication). | `force3ds` (v1), flows frictionless, challenge, none and unspecified, exemptions, external MPI, a Force 3DS routing preset and 3DS cascade (https://docs.solidgate.com/payments/card-payments/3ds-verification/, https://docs.solidgate.com/orchestration/routing-overview/). Liability shift conditions: unknown, check the `eci` and verification result pages under https://docs.solidgate.com. |
| **Risk** | Connections to external fraud providers are documented; an own risk engine: unknown, check https://primer.io/docs. | Own risk or anti-fraud engine: unknown, check https://funnelfox.com/docs (not found in the pages reviewed; this is not a statement that none exists). | Radar: ML model, Stripe managed rules and account rules, with actions such as block, review and request 3DS (https://docs.stripe.com/radar/rules). | Anti-fraud before authorization: decisions Pass, Reject, Force 3DS and Review; lists; rules with aggregation; shadow mode; Solidgate managed rules (https://docs.solidgate.com/risks/fraud/antifraud/). Lists exist in both v1 and v2; which is authoritative: unknown, check the OpenAPI specs. |
| **Billing** | Subscription engine: unknown, check https://primer.io/docs. | Subscription engine owns subscription state and charges through the orchestrator; Solidgate appears as a separate PSP with products and retries on the Solidgate side (billing subscription engine overview and Solidgate integration page, https://funnelfox.com/docs). | Subscriptions, invoices, dunning and Smart Retries (https://docs.stripe.com/billing/subscriptions/overview). | Billing 1.0 (v1) and Billing 2.0 (v2), redemption, smart retries and subscription events (https://docs.solidgate.com/billing/overview/, https://docs.solidgate.com/billing/subscriptions/subscriptions-2.0/billing-events/). |
| **Chargebacks** | A disputes feature tracks disputes across processors (https://primer.io/docs/disputes/overview). | Dispute alerts service with automatic refund before a chargeback (billing disputes page, https://funnelfox.com/docs). | Disputes lifecycle, evidence, and monitoring programs (https://docs.stripe.com/disputes, https://docs.stripe.com/disputes/monitoring-programs). | Stages 1st_chb, 2nd_chb, arbitration; automatic and manual representment; Order Insight, Consumer Clarity, CE3.0 and RDR; v1 operations (https://docs.solidgate.com/risks/chargebacks/, https://docs.solidgate.com/risks/prevention-alerts/prevent/). |
| **Reporting** | Observability dashboards, payment timeline and a Unified Settlement Report (https://primer.io/docs/reconciliation/unified-settlement-report). | Dashboard analytics with a processor filter and a public transactions API (https://funnelfox.com/docs). Metric definitions: unknown, check https://funnelfox.com/docs. | Sigma and Reports (https://docs.stripe.com/sigma, https://docs.stripe.com/reports). | Hub payment and orchestration analytics; operational reports in v1 (JSON) and v2 (async CSV); financial entries (v1); settlements (v2) (https://docs.solidgate.com/reporting/overview/, https://docs.solidgate.com/finance/financial-reports/settlements/). |
| **Webhooks** | Webhook event types and signed delivery (https://primer.io/docs/api-reference/get-started/configure-webhooks). | Inbound processor URLs per organization and outbound targets with a signature header (billing webhook settings page, https://funnelfox.com/docs). Whether the Solidgate integration uses these URLs: unknown, check https://funnelfox.com/docs. | Event destinations, retries, signature verification, unordered delivery (https://docs.stripe.com/webhooks). | v1: `merchant` plus `signature` headers; v2: per-endpoint signature, key rotation, new endpoint starts INACTIVE; ordering not guaranteed (https://docs.solidgate.com/payments/integrate/webhooks/). |

## Notes by domain (distinctions that cause wrong comparisons)

**Payment lifecycle.** Solidgate separates order from transaction, so a metric must declare which of the two (or an attempt) is the grain. Primer, FunnelFox and Stripe use different unit definitions for "approval rate"; confirm each against its own dashboard. Whether a Solidgate block appears as its own order status: unknown, check the lifecycle page.

**Routing.** "Fallback" is a different mechanism on each side: a second authorization inside one payment (Primer), a modified request on the same connector account plus a step sequence (Solidgate fallback and cascade), a backup processor tried before retry (FunnelFox). Do not compare stop lists with trigger lists: one lists what interrupts a cascade, the other what triggers a fallback.

**Retries.** Count retries per layer and per card. Whether a retry is a new payment or the same one differs by provider. Network attempt limits quoted on different pages diverge in scope and date: validate against the card scheme documentation before any policy.

**3DS.** On Solidgate several deciders exist inside one platform (external MPI, exemptions, anti-fraud, API flag, routing preset, SCA, soft decline fallback), so the useful question is which decision the routing log shows as effective. An adaptive 3DS group is a population already declined once: never compare it with a group that did not go through 3DS as if it were an experiment.

**Risk.** Treat blocks and issuer declines as separate classes. Codes 4.05, 4.07 and 4.09 are described differently across Solidgate pages: NEEDS REVIEW. Shadow mode measures rule hits, not approval impact.

**Billing.** There are two modes with one owner each: the funnel tool's engine owns state when it charges through its orchestrator; Solidgate owns it when it is the processor behind the funnel. Two owners exist only during migration or on mixed routes. Redemption is a merchant decision about access; Solidgate imposes no time rule.

**Chargebacks.** Deadlines differ by source and brand; use the per-dispute `deadline_date` as authoritative on Solidgate. Fraud rate on Solidgate is aggregate or cohort based; card scheme programs use their own windows. Do not mix them.

**Reporting.** Reconcile by one base date at a time (authorization, settlement, financial entry `created_at` plus its lag). Settlement basis (gross or net) depends on the provider.

**Webhooks.** v1 and v2 differ in headers, signature algorithm, ordering timestamp and catalog. HTTP 200 is not proof of processing; use delivery logs. A dedupe window is a consumer recommendation, not a vendor guarantee.

## Divergences and items to confirm (not resolved silently)

1. Lifecycle page version: the manifest says v2 while the content references v1 endpoints.
2. Network retry limits differ between the Solidgate error codes page, the Billing page and third-party notes; scope and date differ.
3. Descriptions of Solidgate codes 4.05, 4.07 and 4.09 differ between pages.
4. Subscription cancellation for Solidgate inside FunnelFox: a "coming soon" note in the panel versus an API reference listing Solidgate as supported. The check mark in the PSP comparison table may belong to a different row ("Cancellation funnels").
5. Solidgate webhooks inside FunnelFox: the processor URL list does not include Solidgate, while the integration page says FunnelFox creates webhooks in the Solidgate account; URL, version and events unknown.
6. Billing version used by the FunnelFox integration (1.0 or 2.0): unknown; the retries link on the FunnelFox page uses a path that does not exist in the current Solidgate documentation.
7. Anti-fraud lists exist in v1 and v2; which one is authoritative is unknown.
8. Primer documentation was consulted on a single date; re-check before using it as a contrast in a decision.

### Questions for FunnelFox

1. Does subscription cancellation through the API work today for Solidgate subscriptions, given the panel note?
2. Which URL, version (v1 or v2) and events does FunnelFox register in the Solidgate account when the integration is saved?
3. Does the Solidgate integration use Billing 1.0 or 2.0?

### Questions for Primer

1. Is there a wait or delay action in a Workflow, or another interval-based retry mechanism inside a payment?
2. What is the full catalog of condition attributes and payload fields?
3. Does the final payment status with a fallback consider only the last authorization, and does the documentation state that denominator in writing?

## General gaps

- No call to a live Solidgate API was made.
- Solidgate pages indexed but not read in the original review: connectors, eci, verification result, auto-settle, monitoring programs, risk management analytics, reason codes, refund reasons, countries specifics.
- Commercial proposals (pricing) are outside this matrix.
