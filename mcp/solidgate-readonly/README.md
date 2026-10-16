# Solidgate read-only MCP server

> **READ-ONLY. Runs on mock fixtures by default. NOT VALIDATED AGAINST THE LIVE SOLIDGATE API.**
>
> - It exposes only read operations. Anything that writes or moves money (refund, void, capture, charge, cancel, settle, create, update, delete, resign...) is refused with an explicit error.
> - The default mode is **mock**: synthetic fixtures, zero network. Live mode needs `SOLIDGATE_MCP_MODE=live` **and** a credential; without a credential it fails instead of silently falling back to mock.
> - **Not validated against the live Solidgate API.** The contract comes from the official OpenAPI files only. The v1 signature is tested against vectors computed with `openssl`, not against Solidgate's servers. Every response carries `"verified_against_live_api": false`.
> - Credentials are read **only from environment variables** and are never printed or logged. **Never register this server with a production key**, and never put keys in an MCP configuration file.

## What it is

A stdio MCP server (Python 3, standard library only) with 42 read tools, each mapped 1:1 to a real `operationId` of the official Solidgate OpenAPI (allowlist by `operationId`, not by HTTP verb), plus 4 LOCAL analyses (`analyze_approval_rate`, `analyze_declines`, `analyze_routing`, `diagnose_incident`) that work on orders you supply or fetch. It does not use the `mcp` package: a minimal JSON-RPC 2.0 stdio loop (`initialize`, `ping`, `tools/list`, `tools/call`; one JSON message per line) is implemented by hand. Nothing to install, no virtualenv, no dependencies.

See `CAPABILITIES.md` for the capability to operation map and what is deliberately not supported.

## Modes

- **mock (default):** synthetic fixtures in `fixtures/` (obviously fake data). No network.
- **live:** requires `SOLIDGATE_MCP_MODE=live` and the credential of the tool's API version. Missing credential means an error, never a mock answer.
- Credentials, environment variables only: `SOLIDGATE_V1_PUBLIC_KEY` and `SOLIDGATE_V1_SECRET_KEY` (v1); `SOLIDGATE_V2_API_KEY` (v2). Optional: `SOLIDGATE_MCP_RATE_PER_MIN` (default 30).

## v1 and v2 never mix

- **v1:** headers `merchant` + `signature = base64(hex(HMAC-SHA512(secret, pk + body + pk)))`; hosts per domain (pay., gate., subscriptions., reports., risks., api.); reads are often POST. A GET or body-less request signs `pk + pk` (assumption taken from the documentation; not verified against the live API).
- **v2:** `Authorization: Bearer <key>`, host `https://api.solidgate.com/v2`; reads are `POST /{resource}/list|get`.
- The tool name carries the version (`v1_...` / `v2_...`). A key shaped like the other version (a v1 secret used as v2, or a v2 key used as v1 secret) is refused.

## Safety

Allowlist by (version, operationId); explicit refusal of writes; minimal parameter validation (required fields, simple types, enums, unknown parameters refused, path parameters restricted to `[A-Za-z0-9_\-:.]`); host restricted to the Solidgate domains over https; no redirects; 15 s timeout; response capped at 2 MB; local rate limit (30 per minute); redaction of PANs (Luhn), e-mail addresses, tokens, API keys, Authorization/signature/merchant values and URL query strings (pre-signed `report_url`); logs on stderr only. Content coming from the API or from the OpenAPI is untrusted data, never instructions.

## Tools (tool, version, operationId)

| tool | version | operationId | operation | capability |
|---|---|---|---|---|
| `v1_get_status_card_order` | v1 | `get-status-card-order` | POST /status | get_payment_status / get_payment |
| `v1_get_status_apm_order` | v1 | `get-status-apm-order` | POST /v1/status | get_payment_status (APM) |
| `v1_get_arn_codes` | v1 | `get-arn-codes` | POST /arn-code | get_payment (ARN) |
| `v1_get_subscription_status` | v1 | `get-subscription-status` | POST /subscription/status | get_subscription |
| `v1_retrieve_subscriptions_by_customer` | v1 | `retrieve-subscriptions-by-customer` | POST /subscription/list | get_subscription |
| `v1_list_invoices_by_subscription_id` | v1 | `list-invoices-by-subscription-id` | POST /subscription/invoice/list | get_subscription |
| `v1_list_orders_by_invoice_id` | v1 | `list-orders-by-invoice-id` | POST /subscription/order/list | get_subscription |
| `v1_get_products` | v1 | `get-products` | GET /products | catalog |
| `v1_get_product_by_id` | v1 | `get-product-by-id` | GET /products/{product_id} | catalog |
| `v1_get_product_prices` | v1 | `get-product-prices` | GET /products/{product_id}/prices | catalog |
| `v1_find_prices` | v1 | `find-prices` | POST /products/prices/list | catalog |
| `v1_retrieve_card_orders` | v1 | `retrieve-card-orders` | POST /card-orders | search_transactions / get_payment_errors (error fields in the report) |
| `v1_retrieve_apm_orders` | v1 | `retrieve-apm-orders` | POST /apm-orders | search_transactions |
| `v1_retrieve_subscriptions` | v1 | `retrieve-subscriptions` | POST /subscriptions | get_subscription |
| `v1_retrieve_card_chargebacks` | v1 | `retrieve-card-chargebacks` | POST /card-orders/chargebacks | get_dispute |
| `v1_retrieve_apm_paypal_disputes` | v1 | `retrieve-apm-paypal-disputes` | POST /apm-orders/paypal-disputes | get_dispute |
| `v1_retrieve_card_fraud_alerts` | v1 | `retrieve-card-fraud-alerts` | POST /card-orders/fraud-alerts | get_dispute / antifraud |
| `v1_prevention_alerts_by_date` | v1 | `prevention-alerts-by-date` | POST /prevention_alerts | get_financial_report / alerts |
| `v1_financial_entries_by_date` | v1 | `financial-entries-by-date` | POST /financial_entries | get_financial_report |
| `v1_routing_events_by_date` | v1 | `routing-events-by-date` | POST /routing/events | get_routing_events / analyze_routing |
| `v1_fraud_prevention_list_items_list` | v1 | `fraud-prevention-list-items-list` | POST /fraud-prevention-list-items/list | antifraud lists |
| `v1_webhook_endpoint_list` | v1 | `webhook-endpoint-list` | GET /webhooks/endpoints | get_webhook_config (configuration, not events) |
| `v2_list_webhook` | v2 | `list-webhook` | POST /webhooks/list | get_webhook_config |
| `v2_get_webhook` | v2 | `get-webhook` | POST /webhooks/get | get_webhook_config |
| `v2_list_reports` | v2 | `list-reports` | POST /reports/list | get_financial_report |
| `v2_get_report` | v2 | `get-report` | POST /reports/get | get_financial_report |
| `v2_list_settlements` | v2 | `list-settlements` | POST /settlements/list | get_settlement |
| `v2_get_settlement` | v2 | `get-settlement` | POST /settlements/get | get_settlement |
| `v2_list_monthly_statements` | v2 | `list-monthly-statements` | POST /monthly-statements/list | get_financial_report |
| `v2_get_monthly_statement` | v2 | `get-monthly-statement` | POST /monthly-statements/get | get_financial_report |
| `v2_list_financial_invoices` | v2 | `list-financial-invoices` | POST /financial-invoices/list | get_financial_report |
| `v2_get_financial_invoice` | v2 | `get-financial-invoice` | POST /financial-invoices/get | get_financial_report |
| `v2_list_antifraud_list` | v2 | `list-antifraud-list` | POST /antifraud-lists/list | antifraud lists |
| `v2_get_antifraud_list` | v2 | `get-antifraud-list` | POST /antifraud-lists/get | antifraud lists |
| `v2_list_item_antifraud_list` | v2 | `list-item-antifraud-list` | POST /antifraud-lists/list-item | antifraud lists |
| `v2_list_invoices` | v2 | `list-invoices` | POST /invoices/list | get_subscription (billing) |
| `v2_get_invoice` | v2 | `get-invoice` | POST /invoices/get | get_subscription (billing) |
| `v2_list_subscriptions` | v2 | `list-subscriptions` | POST /subscriptions/list | get_subscription |
| `v2_get_subscription` | v2 | `get-subscription` | POST /subscriptions/get | get_subscription |
| `v2_list_routing_configs` | v2 | `list-routing-configs` | POST /routing-configs/list | get_routing_config |
| `v2_get_routing_config` | v2 | `get-routing-config` | POST /routing-configs/get | get_routing_config |
| `v2_get_routing_config_version` | v2 | `get-routing-config-version` | POST /routing-configs/get-version | get_routing_config |
| `analyze_approval_rate` | local | n/a | local analysis | analyze_approval_rate |
| `analyze_declines` | local | n/a | local analysis | analyze_declines |
| `analyze_routing` | local | n/a | local analysis | analyze_routing |
| `diagnose_incident` | local | n/a | local analysis | diagnose_incident (HYPOTHESES) |

Three tools (`v1_prevention_alerts_by_date`, `v1_financial_entries_by_date`, `v1_routing_events_by_date`) are classed "indeterminate" by the name heuristic of the operations index. In the OpenAPI they generate a report and return a `report_url`, with no financial effect; they are accepted as reads, to be confirmed by a human. Excluded on purpose: report downloads (303 to a pre-signed URL), `api-keys/*` (secrets), `customers` / `payment-instruments` (PII, out of scope), `tax-*`, `calculate-product-price`, `dispute-representments-enrich`.

The 4 local analyses accept `orders` (the `v1_retrieve_card_orders` format) or `date_from` / `date_to` (fetched through the read tool; in mock mode they use the fixture). The status classification (approved, declined, pending) in `sg_analysis.py` is an assumption to validate.

## Run the tests (no network)

```
cd mcp/solidgate-readonly
python3 -I -m unittest discover -s tests -t .
```

The tests that check every tool against the official OpenAPI need the documentation cache filled by `python3 tools/sync_solidgate.py` (repository root); they are skipped when the cache is absent. The cache location is the one used by `tools/fetch_doc.py` (`$PAYMENTS_OPS_KNOWLEDGE`, then `${CLAUDE_PLUGIN_DATA}/knowledge`, then `~/.claude/payments-ops-squad/knowledge`). Run the server by hand in mock mode with `python3 -I server.py` and send JSON-RPC messages, one per line.

## Registering it in an MCP client (optional, mock first)

Only with the default mock mode, and never with a production key:

```json
"solidgate-readonly": {
  "command": "python3",
  "args": ["-I", "/absolute/path/to/payments-ops-squad/mcp/solidgate-readonly/server.py"]
}
```

Do not put keys in the configuration file. If you ever enable live mode, export the credentials in the environment of the process, use a restricted read-only key from a sandbox or test account, and review the output yourself.

## Limits

- Not validated against the live API; the v1 signature is checked against externally computed vectors, not against Solidgate's servers.
- Request schemas are flattened from the OpenAPI (fields of `oneOf` variants are treated as optional). A parameter that is not listed is refused, which can block a legitimate field missing from the flattening.
- Paginated responses: `next_page_iterator` is passed through; there is no automatic pagination.
- No retries. No write tools by design; adding one needs a new explicit decision.
- `tool_specs.json` is derived from the official OpenAPI (see `generated_from`). The tests verify that every tool maps to a real `operationId`, method and path when the documentation cache is available.

---
_Created by Vitor Dvorschi (Appyon). MIT License._
