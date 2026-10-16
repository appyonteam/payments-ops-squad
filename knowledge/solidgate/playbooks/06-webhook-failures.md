> Status: draft. Not yet validated against a live Solidgate account.

# 06. Webhook failures

Common rules: see `README.md`. Supports scenarios **A** (diverging state) and **D** (recurring events).

## 1. Objective
Diagnose Solidgate events that are missing, duplicated, out of order or rejected (signature, version, endpoint), without mixing the v1 contract with v2 and without confusing "HTTP 200 returned" with "event processed".

## 2. Symptoms
- An order or subscription with a different state in Solidgate and in the merchant system.
- Access granted or revoked at the wrong time (renewal, redemption, unpaid).
- Deliveries rejected for an invalid signature; exhausted retries; duplicated events.
- A v1 to v2 switch with no events arriving.

## 3. Required data
Solidgate webhook logs (event, notification, attempt, status, body and response); merchant endpoint logs (status returned, response time); `solidgate-event-id`, `solidgate-event-type` and `solidgate-event-created-at` (v1) or `solidgate-event-occurred-at` (v2); endpoint configuration (version, channel, active or inactive, channel scope); date of the last secret rotation. Without authorized access to the Hub or logs, the playbook stops at "Gaps".

## 4. Sources
- `<cache>/solidgate/docs/payments/integrate/webhooks.md` (v1 vs v2, how it works, logs, event handling)
- `<cache>/solidgate/docs/billing/subscriptions/subscriptions-2.0/billing-events.md` (events and access action)
- `<cache>/solidgate/docs/billing/subscriptions/subscriptions-1.0/subscription-insights/subscription-events.md`
- `<cache>/solidgate/docs/payments/integrate/access-to-api.md`
- The Solidgate OpenAPI specs (webhook operations in v1 and v2, including `create-webhook` and `rotate-webhook-key`)
- Other providers: Stripe webhooks and events (https://docs.stripe.com/webhooks), Primer webhooks (https://primer.io/docs/api-reference/get-started/configure-webhooks), FunnelFox billing webhooks (https://funnelfox.com/docs)

## 5. Tools
`solidgate-incident-investigator` (lead), `solidgate-api-architect` (v1 vs v2 contract, signature), `solidgate-billing` (subscription events); `primer-integrations` and `funnelfox-integrations` for the path used by the user's current stack (in some stacks the funnel tool receives processor webhooks); `stripe-payments` as methodology (idempotency, ordering, signature).

## 6. Procedure (read only)
1. Identify the endpoint version (v1 or v2) and confirm the consumer uses the same contract: v1 with `merchant` plus `signature` (HMAC-SHA512 with the webhook public and secret keys); v2 with `signature` (HMAC-SHA256 of the endpoint). Never validate one with the logic of the other.
2. Open the delivery log: filter by event, channel, status and Event ID or Notification ID; see the attempt, response and body. The documentation treats this as the first diagnostic step.
3. If there are no attempts: was the v2 endpoint created INACTIVE? Does the channel scope exclude the channel? Is the event not subscribed? (v2 returns `EVENT_TYPES_NOT_FOUND` for an unsupported type.)
4. If attempts failed: a non-2xx response within the timeout (30 s on v1)? An invalid signature? A certificate problem? Failed deliveries are retried up to 8 times, with intervals growing from 15 minutes to 24 hours.
5. If duplicates exist: check `solidgate-event-id` and the consumer's deduplication policy (keeping IDs for up to a week is a recommendation to the consumer).
6. If out of order: sort by `solidgate-event-created-at` (v1) or `solidgate-event-occurred-at` (v2), never by arrival; process through a queue.
7. For subscriptions: check the access rule by subscription status and invoice status (billing events) and the use of `billing_reason: subscription_cycle` for renewal.
8. If a funnel or orchestrator sits between Solidgate and the system of record, verify how it receives or relays Solidgate events; if undocumented, mark it NOT VERIFIED.

## 7. Decision criteria
- Delivery failure (Solidgate did not send or the endpoint is inactive) vs processing failure (sent, but the consumer erred) vs contract failure (version or signature).
- An event missing after 8 attempts: reconcile by a status query (read), never by blind reprocessing.
- A duplicate is an incident only if it produced a side effect (access, e-mail, duplicated commission).

## 8. Hypotheses
- H1 A v2 endpoint remains INACTIVE. Validate in the log and configuration.
- H2 The consumer validates a v1 signature on a v2 event, or the reverse. Validate the header.
- H3 A slow response or 5xx exhausted the attempts. Validate in the log.
- H4 The body was altered before signature verification. Validate in the verification code (raw body).
- H5 Out-of-order events applied by arrival. Validate the ordering policy.
- H6 A secret was rotated and the grace period expired. Validate the rotation date.

## 9. Expected evidence
A log line with attempt and response; a sample of events by type and ID; a comparison of the Solidgate state (by query) with the consumer state; a snippet of the signature verifier (without secrets).

## 10. Recommendations
Proposals: a queue plus idempotency by `solidgate-event-id`, ordering by event timestamp, a fast 2xx with asynchronous processing, an alarm for failed deliveries, a v1 to v2 switch checklist covering path, header, signature and event catalog. Secret rotation and endpoint creation are write actions and need approval.

## 11. Impacts and risks
Wrongly granted or denied access, charges without provisioning, duplicated partner commissions, accounting divergence; a security risk if the signature is not verified; the risk of a blind consumer during a version migration.

## 12. Suggested tests
In the Solidgate sandbox: create a subscription and complete the first payment with a test card to provoke `SUBSCRIPTION_ACTIVATED`; use the recurring decline test card to provoke `INVOICE_PAYMENT_FAILED`, `SUBSCRIPTION_REDEMPTION_STARTED` and `SUBSCRIPTION_UNPAID`; a unit test of the verifier with vectors for each version.

## 13. Completion criteria
Endpoint version and contract confirmed; failure class (delivery, processing, contract) identified with a log; Solidgate state and consumer state reconciled; migration checklist delivered; gaps (Hub access, relay mechanism of any intermediary) declared.
