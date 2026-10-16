> Status: draft. Not yet validated against a live Solidgate account.

# 04. Routing diagnosis

Common rules: see `README.md`. Main scenario: **C** (which connector is best). Supports **A** and **E**.

## 1. Objective
Read the Solidgate routing configuration (channel, method group, preset, rule, split, segment, step), explain why a payment went to a connector, and compare connectors and connector accounts on a valid basis, without treating "highest raw rate" as "best".

## 2. Symptoms
- Approval differs between connectors or connector accounts.
- Unexpected volume concentration on one connector; split weights differ from the configured ones.
- Skipped steps (`SKIP_*`) in volume; payments blocked by routing (0.04).
- An approval change coincides with a version publication.

## 3. Required data
Active configuration and versions (read via API v2: `get-routing-config`, `list-routing-configs`, `get-routing-config-version`; or a configuration export from the Hub); routing events (v1: `routing-events-by-date`, `download-routing-events`); orders with connector, connector account, descriptor, step, route, version; mix by country, brand, BIN, card type, amount, CIT or MIT; whether Smart Splitting is active.

## 4. Sources
- `<cache>/solidgate/docs/orchestration/routing-overview.md` (components, presets, rules, splits and Smart Splitting, cascade and fallbacks)
- `<cache>/solidgate/docs/orchestration/track-routing/trace-routing-decisions.md`, `monitor-routing-analytics.md`, `inspect-routing-configurations.md`, `export-routing-events.md`
- `<cache>/solidgate/docs/orchestration/connectors.md` (indexed, not read in the original review: NOT VERIFIED)
- `<cache>/solidgate/docs/payments/payments-insights/channel-routing-details.md`
- The Solidgate OpenAPI specs, v1 and v2 (routing operations)
- Comparison: Primer Workflows (https://primer.io/docs/workflows/overview), FunnelFox payments orchestration (https://funnelfox.com/docs)

## 5. Tools
`solidgate-routing` (lead), `solidgate-payment-performance`, `solidgate-incident-investigator` (sudden change), `solidgate-api-architect` (v2 read contract); `primer-workflows` and `funnelfox-orchestration` for the user's current stack; `stripe-payments` as methodology for slicing.

## 6. Procedure (read only)
1. Map the configuration: channel, method group (cards, wallets, merchant-managed network tokens, Solidgate tokens), preset (Block, Force 3DS, All other), rules by priority (the first match wins), splits (sum to 100%) and cascade steps.
2. Record the active version, publication date and prior version; confirm only one configuration is active per channel and group.
3. For one order, read the routing log: selected step, skipped steps and reason, payment blocked, 3DS decision.
4. Rebuild the entry: the population that matched the rule, with `Initial Connector Account ID`, before reading results by final connector.
5. Compare connectors within the same segment (BIN country, brand, type, amount band, CIT or MIT), never in aggregate; declare n per cell.
6. If Smart Splitting is active, treat weights as time-varying (recalculated on a fixed cadence when enough new data exists) and filter by version, route and segment.
7. Evaluate the cascade by the conversion of the step set, not by a single step.
8. Write the nine-section answer; list what could not be read.

## 7. Decision criteria
- "Best connector" only with a sustained difference in a comparable segment, sufficient n, equal window and a control; otherwise "no evidence of a difference".
- A difference is attributed to routing only if it coincides with a version or rule change and disappears under control.
- A connector with frequent `SKIP_*` is an eligibility problem (currency, brand, 3DS, external MPI), not a performance problem.
- A weight change under Smart Splitting is not a configuration change by the merchant.

## 8. Hypotheses
- H1 The difference between connectors is a mix effect. Validate by segment.
- H2 A new version changed rule order. Validate by version diff.
- H3 Smart Splitting shifted traffic. Validate with the weight series.
- H4 A connector was skipped for incompatibility (currency, 3DS, MPI). Validate with the skip reason.
- H5 A fallback-only account inherits the decline of the origin route. Validate by entry.

## 9. Expected evidence
A version diff; a table segment x connector x n x approval with an interval; a distribution of skip reasons; a split weight series; a sample of orders with routing logs.

## 10. Recommendations
Proposals: an A/B test with fixed splits (Smart Splitting off in the control arm, by human decision) to rank connectors; reorder steps by eligibility; review the rule preset. No configuration change is executed; publishing a version is a write action needing named approval.

## 11. Impacts and risks
Revenue and cost per connector (pricing is outside this base); risk of duplicating routing decisions with Primer or FunnelFox; risk of concentrating volume on one account; card scheme monitoring risk if traffic moves to another acquirer.

## 12. Suggested tests
Shadow comparison in the sandbox with test cards per brand; replay of a sample of orders against the rule (check that the described rule matches the observed connector); a rule-order test (first match wins) in a test environment.

## 13. Completion criteria
Configuration and version recorded; every connector comparison has segment, n, window and control; skip reasons explained; data and method limitations declared; no ranking by raw rate.
