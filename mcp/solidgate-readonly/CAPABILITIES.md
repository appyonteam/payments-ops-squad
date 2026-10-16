# CAPABILITIES: desired capability vs real operation

Rule: a capability becomes a tool only when it maps to a real `operationId` in the official Solidgate OpenAPI. An analysis without an endpoint is LOCAL; anything else is "not supported". Everything here is NOT VALIDATED AGAINST THE LIVE API.

| Desired capability | Status | Real operation (tool) | Note |
|---|---|---|---|
| get_payment | Supported (partial) | `v1_get_status_card_order` (get-status-card-order), `v1_get_arn_codes`, `v1_retrieve_card_orders` | There is no full "get order" call: status by order_id, and a report by period. v2 has no payment operation. |
| search_transactions | Supported | `v1_retrieve_card_orders`, `v1_retrieve_apm_orders` | Search by date window (report), not by free text. |
| get_payment_status | Supported | `v1_get_status_card_order`, `v1_get_status_apm_order` | |
| get_payment_errors | Local analysis | `v1_retrieve_card_orders` (field `error_code`) + `analyze_declines` | There is no errors endpoint; the meaning of the codes comes from the documentation. |
| analyze_declines | Local analysis | `analyze_declines` | Over orders that were read or supplied. |
| analyze_approval_rate | Local analysis | `analyze_approval_rate` | The status classification is an assumption to validate. |
| get_routing_config | Supported (v2) | `v2_list_routing_configs`, `v2_get_routing_config`, `v2_get_routing_config_version` | |
| analyze_routing | Local analysis | `analyze_routing` + `v1_routing_events_by_date` (generates a report, returns `report_url`) | The events report is a file; the local analysis uses the cascade present in the orders. |
| get_webhook_events | NOT supported by the API | n/a | Webhook events are pushed; there is no operation to query them. Endpoint configuration: `v1_webhook_endpoint_list`, `v2_list_webhook`, `v2_get_webhook`. |
| get_subscription | Supported | v1: `v1_get_subscription_status`, `v1_retrieve_subscriptions_by_customer`, `v1_list_invoices_by_subscription_id`, `v1_list_orders_by_invoice_id`, `v1_retrieve_subscriptions`; v2: `v2_get_subscription`, `v2_list_subscriptions`, `v2_get_invoice`, `v2_list_invoices` | Subscriptions 1.0 (v1) and 2.0 (v2) are different products; confirm which one the account uses. |
| get_dispute / chargebacks | Supported | `v1_retrieve_card_chargebacks`, `v1_retrieve_apm_paypal_disputes`, `v1_retrieve_card_fraud_alerts` | Creating or enriching a representment is a write: out. v2 has no disputes. |
| get_settlement | Supported (v2) | `v2_list_settlements`, `v2_get_settlement` | Needs an account-level key (per the OpenAPI description). |
| get_financial_report / reports | Supported | v2: `v2_list_reports`, `v2_get_report`, `v2_list_monthly_statements`, `v2_get_monthly_statement`, `v2_list_financial_invoices`, `v2_get_financial_invoice`; v1: `v1_financial_entries_by_date`, `v1_prevention_alerts_by_date` | `v2 reports/create` is a write (out); `reports/download` (303 to a pre-signed URL) is excluded. |
| antifraud lists | Supported | `v1_fraud_prevention_list_items_list`, `v2_list_antifraud_list`, `v2_get_antifraud_list`, `v2_list_item_antifraud_list` | Creating, changing or removing an item is a write: out. |
| diagnose_incident | Local analysis | `diagnose_incident` | Returns HYPOTHESES for approval-rate drops; not a confirmed diagnosis. |
| product and price catalog | Supported (extra) | `v1_get_products`, `v1_get_product_by_id`, `v1_get_product_prices`, `v1_find_prices` | |
| refund, void, capture, charge, cancel, settle, resign, create/update/delete | REFUSED by design | n/a | Writes and financial effects are outside the scope of this MCP. |
| api-keys, customers, payment-instruments, tax, report download | Deliberately excluded | n/a | Secrets, PII or out of scope; reassess only with an explicit decision. |

---
_Created by Vitor Dvorschi (Appyon). MIT License._
