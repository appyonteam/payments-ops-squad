> Status: draft. Not yet validated against a live Solidgate account.

# 10. Financial reconciliation

Common rules: see `README.md`. Supports scenarios **A** (approved vs settled sales) and **E** (volume comparison between orchestrators).

## 1. Objective
Close, in read mode, the path approved sale, settlement, payout, bank statement on Solidgate, with unit, base date and basis (gross or net) declared, and compare it with what you already use on Primer (Unified Settlement Report) and Stripe (payout reconciliation). Reconciliation never assumes that "approved" means "settled".

## 2. Symptoms
- The sum of approved sales differs from the settlement or payout.
- Date differences between authorization, settlement and the financial entry `created_at`.
- Fees, chargebacks, RDR, reserves or adjustments without a matching line.
- Sale currency differs from payout currency; an unexplained exchange rate.
- Partner or affiliate commission without an origin, if the business pays one.

## 3. Required data
Settlements (v2: list and SETTLEMENT and FINANCIAL_ENTRIES files), financial entries (v1: by `created_at`, 4 hour lag, available for 30 days), order and chargeback reports per period, bank statement, provider table (provider, legal entity, period), sale and payout currency, settlement basis (gross or net), reserves. Without authorized access to the reports, the playbook stops at "Gaps".

## 4. Sources
- `<cache>/solidgate/docs/finance/financial-reports/settlements.md` (gross vs net, providers and availability, API v2)
- `<cache>/solidgate/docs/finance/financial-reports/financial-entries.md`
- `<cache>/solidgate/docs/finance/financial-reports.md`, `monthly-reports.md`, `financial-invoices.md`, and `<cache>/solidgate/docs/finance/commissions.md`
- `<cache>/solidgate/docs/reporting/overview.md` and `create-reports.md` (v1 JSON vs v2 CSV)
- The Solidgate OpenAPI specs (`list-settlements`, `get-settlement`, `list-monthly-statements`, `get-monthly-statement`, `list-financial-invoices`, `financial-entries-by-date`, `download-financial-entries`)
- Comparison: Primer Unified Settlement Report (https://primer.io/docs/reconciliation/unified-settlement-report), Stripe reports and Sigma (https://docs.stripe.com/reports, https://docs.stripe.com/sigma)

## 5. Tools
`solidgate-reconciliation` (lead), `solidgate-chargebacks` (chargeback and RDR lines), `solidgate-payment-performance`; `primer-integrations` and `funnelfox-api` for the user's current stack; `stripe-finance` as methodology. Economics (pricing, margin) is outside this base.

## 6. Procedure (read only)
1. Fix unit and base date per report: authorization (approval volume), settlement (gross volume), financial entry `created_at` (plus 4 hours) and payout date. Never add numbers from different bases.
2. Build the position (settlements by period, provider, legal entity, currency) separately from the flow (financial entries per transaction); every number closes against the source screen or file.
3. Verify the settlement basis (gross or net) per provider; fees charged later do not appear in a gross payout.
4. Close by record type: sales, refunds, chargebacks, RDR, fees, reserves and adjustments; flag what has no line.
5. Extend the query interval past month end to absorb the 4 hour lag; filter afterwards by transaction date.
6. Check sale currency vs payout currency and the exchange rate applied; compare with the bank statement.
7. Check the retention cycle: files expire (financial entries 30 days; `download_url` is short-lived; status PROCESSING needs a new query).
8. Cross with your own order base by order identifier, treating a declined renewal separately from a paid order.
9. Write the nine-section answer.

## 7. Decision criteria
- A difference is explained when classified (timing, fee, exchange, reserve, chargeback, refund) and the sum closes; an unexplained difference is an open incident.
- Reconcile by value, with currency declared, never by count.
- Any payout divergence goes to `solidgate-incident-investigator`.

## 8. Hypotheses
- H1 The difference is a base date (authorization vs settlement vs `created_at`). Validate by aligning dates.
- H2 Gross vs net basis explains the fee difference. Validate by the settlement provider.
- H3 A chargeback or RDR has no line because of lag. Validate in the next period's entries.
- H4 Exchange and payout currency. Validate by the rate applied.
- H5 A reserve is held. Validate by record type.
- H6 A duplicated order, or a declined renewal counted as an order. Validate by key.

## 9. Expected evidence
A bridge table (sales, adjustments, payout) with each line citing its source file and line; an explained or open residual; a table by provider and legal entity; a list of expired files.

## 10. Recommendations
Proposals: a daily read of financial entries and a weekly read of settlements, a single reconciliation key, a residual alert above a threshold set by the owner, a file retention policy. Creating reports and schedules is a write action outside this playbook (named approval).

## 11. Impacts and risks
Accounting close, partner commissions, the risk of reconciling on the wrong basis, the risk of losing an expired file, cross-entity regulatory risk. Whether Solidgate pays out in a given currency is something to verify with the vendor, not assume.

## 12. Suggested tests
A retroactive reconciliation of a closed period already checked against a bank statement (with authorized data); a month-boundary edge test (a late-night transaction on the last day); a cross-currency test; a test with a file in PROCESSING.

## 13. Completion criteria
A bridge from sale to payout closing with zero or classified residual; units and dates declared; source files referenced; open divergences recorded; the `monthly-reports.md` and `financial-invoices.md` pages read or the gap declared.
