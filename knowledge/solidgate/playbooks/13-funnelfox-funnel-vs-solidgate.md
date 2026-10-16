> Status: reviewed against the official documentation (2026-10-09). Not validated against a live account.

# 13. FunnelFox funnel vs Solidgate

Common rules: see `README.md`. Supports scenarios **D** (recurring revenue inside the funnel) and **E**. A mixed topic: a FunnelFox and Solidgate integration involves `funnelfox-payments`, `funnelfox-integrations` and the Solidgate specialists, with closing sections "FUNNELFOX SQUAD APPLIED" and "SOLIDGATE SQUAD APPLIED".

## 1. Objective
Understand what changes in the funnel and checkout when Solidgate enters through FunnelFox (as a processor inside the funnel) or in place of the FunnelFox, orchestrator and processors path, separating two modes, each with one owner of subscription state: the FunnelFox subscription engine (which charges through its orchestrator), or Solidgate as PSP and Billing (Solidgate is the owner and the FunnelFox retry logic does not apply; two owners exist only during a migration or on mixed routes). List what the funnel loses or gains.

## 2. Symptoms
- A question about "using Solidgate inside FunnelFox" or "replacing the orchestrator".
- A funnel feature missing with Solidgate (intro offers, promo codes, subscription upgrade).
- Duplicate subscriptions by e-mail, a wallet that does not appear, cancellation that does not work.
- Divergence between what the FunnelFox page says and what Solidgate documents.

## 3. Required data
Funnel configuration (checkout element, products, currencies, trials, upsells, wallet button), integration (Sandbox and Live channels, Solidgate keys and webhooks by name only, never value), Solidgate product catalog per currency, Billing version used, cancellation flow, events received by FunnelFox. Without access to the FunnelFox and Solidgate panels the playbook is documentary.

## 4. Sources
- FunnelFox Solidgate integration page (features, setup, products and currencies, wallets, "Limit One Subscription per Email", testing) and the payments integration index with the PSP comparison table (https://funnelfox.com/docs)
- FunnelFox wallet button, pricing localization, subscription management pages, the cancel subscription API reference, the billing subscription engine overview, billing webhook settings and the billing webhooks developer page (https://funnelfox.com/docs)
- Solidgate: `<cache>/solidgate/docs/billing/overview.md`, `<cache>/solidgate/docs/billing/subscriptions/subscriptions-2.0/billing-events.md`, `<cache>/solidgate/docs/payments/integrate/payment-form/apple-pay-button.md`, `<cache>/solidgate/docs/payments/integrate/webhooks.md`

## 5. Tools
`solidgate-api-architect` (Solidgate lead), `solidgate-billing`, `solidgate-payment-performance`; `funnelfox-payments` and `funnelfox-integrations` (FunnelFox leads), `funnelfox-billing`, `funnelfox-api`, `funnelfox-orchestration`, `funnelfox-3ds`, `funnelfox-retries`; Stripe skills as methodology.

## 6. Procedure (read only)
1. Identify the mode: (a) Solidgate as a processor inside FunnelFox (products created in Solidgate and synced to the funnel; Solidgate is the catalog source); (b) Solidgate in place of the FunnelFox, orchestrator and processors path; (c) Solidgate behind the orchestrator. Each mode changes who owns subscription state, dunning, 3DS and routing.
2. List funnel capabilities per PSP from the FunnelFox comparison table. With Solidgate, subscriptions, trials, a second-subscription upsell, one-time purchases and wallets are listed; subscription upgrade, intro offers and promo codes are not. Re-check the current page.
3. Record checkout behavior differences: one Solidgate product per currency; Apple Pay renders only in Safari; a single Solidgate wallet source per screen; Apple Pay needs domain verification; the "Limit One Subscription per Email" toggle blocks a new purchase before Solidgate is called.
4. Reconcile documentation divergences. Cancellation: the check mark in the PSP comparison table may belong to the "Cancellation funnels" row (a retention funnel), not to subscription cancellation. The real divergence to verify is panel vs API: a "coming soon" note for Solidgate in subscription management versus an API reference that lists Solidgate as supported. Webhooks: Solidgate may be absent from the list of FunnelFox processor webhook URLs while the integration page says FunnelFox creates webhooks in the Solidgate account; the URL, version (v1 or v2) and events are NOT VERIFIED. Do not choose: mark NEEDS REVIEW and ask FunnelFox.
5. Verify which Solidgate Billing version FunnelFox uses (1.0 or 2.0): NOT VERIFIED (hypothesis: 1.0; a weak hint is that the retries link on the FunnelFox page points to a Billing 1.0 style path).
6. Map retry layers and the dunning owner in the chosen mode: in the FunnelFox Billing mode, the funnel tool's retry logic, Stripe Billing and the orchestrator; in the Solidgate-as-PSP mode, retries sit on the Solidgate side and the FunnelFox retry logic does not apply. The chain in the Solidgate mode (a hypothesis anchored on these facts): FunnelFox (funnel, synced catalog) → Solidgate (Billing, retry, 3DS, processing, webhooks) → network and issuer, with the orchestrator outside. Map the 3DS decider as well (adaptive 3DS in FunnelFox needs the orchestrator; in the Solidgate integration, 3DS belongs to Solidgate).
7. List migration dependencies: vault and tokens, alert descriptors (Ethoca, RDR), any partner payout dependency on the current processor, dual operation; without quantifying (there is no technical scope or quote).
8. Write the nine-section answer, with a section per family.

## 7. Decision criteria
- A funnel feature essential to the business that is absent with Solidgate (for example promo codes, upgrade) is a blocker or needs redesign; the decision belongs to the owner.
- Two owners of subscription state are not acceptable in production; choose one per route.
- Any mode that forces leaving a structural dependency (for example partner payouts on the current processor) without an alternative is a structural blocker.
- An unresolved documentation divergence prevents any statement about behavior: ask the FunnelFox team.

## 8. Hypotheses
- H1 The Solidgate integration inside FunnelFox covers the main flow but loses offers (intro, coupon, upgrade). Validate against the current funnel design.
- H2 Solidgate as catalog source conflicts with versioned price points in FunnelFox. Validate with `funnelfox-billing`.
- H3 Dunning is duplicated (FunnelFox and Solidgate) only during migration or on mixed routes; in the Solidgate-as-PSP mode the owner is Solidgate. Validate the owner.
- H4 3DS gets a new decider on the route. Validate the evaluation order.
- H5 A partner payout dependency prevents changing the route. Validate the dependency.

## 9. Expected evidence
A capability x PSP table with sources; a list of documentation divergences with sources on both sides; an owner map (state, dunning, 3DS, routing, webhooks) per mode; a list of migration dependencies with no invented number.

## 10. Recommendations
Proposals: treat mode (a) as an evaluation of an additional processor in a test funnel, not a replacement; confirm the three divergences in writing with FunnelFox and Solidgate; ask for an official invoice-by-invoice simulation before any switch decision. Nothing is configured by this playbook.

## 11. Impacts and risks
Funnel conversion (missing offers, restricted wallet), recurring revenue, partner payouts, operations (two systems during wind down), compliance (descriptor, alerts), and the risk of deciding on an outdated integration page.

## 12. Suggested tests
In the sandbox (Solidgate Sandbox channel and the test cards cited on the FunnelFox page, no production): success, recurrence and decline; the duplicate subscription toggle; Apple Pay on Safari and non-Safari; cancellation by the documented path and by API; end to end webhook receipt.

## 13. Completion criteria
Integration mode defined or the open question recorded; capability and owner tables delivered; documentation divergences open with an owner; structural dependencies listed; no statement about cancellation, webhooks or Billing version without a source.
