---
name: radar-fraud-rules
description: "Designs and audits Stripe Radar fraud rules — block prepaid, 3DS, risk levels, lists, and decline patterns. Use when the user mentions \"Radar\", \"fraud rules\", \"block prepaid\", \"3D Secure\", \"high risk payments\", or \"reduce fraud\". For funding mix data, see card-funding-risk."
metadata:
  version: 1.0.0
---

> Adapted by Vitor Dvorschi (Appyon) from [appeeky/stripe-skills](https://github.com/appeeky/stripe-skills) (MIT License, (c) 2026 Erencan).

# Radar & Fraud Rules

## Stripe MCP Setup

Requires **Stripe MCP** connected via OAuth or restricted key. Docs: https://docs.stripe.com/mcp

1. `GetMcpTools` with `server: "user-Stripe"` (or `plugin-stripe-stripe`) before any call
2. Prefer `stripe_api_search` → `stripe_api_details` → `stripe_api_read` for list/retrieve
3. **Always paginate** — `limit: 100`, follow `has_more` with `starting_after`
4. Amounts are in **cents** unless noted
5. Never expose secret keys in output

## Assess Current Rules

Dashboard: **Radar → Rules**. Document enabled vs disabled.

Default rules often include:
- Block `risk_level = highest`
- Default block lists
- 3DS / CVC / postal (often disabled)

Custom rules require **Radar for Fraud Teams**.

## Recommended Rules (SaaS subscriptions)

| Priority | Rule | Action |
|----------|------|--------|
| 1 | `:card_funding: = 'prepaid'` | Block |
| 2 | `:is_new_card_on_customer:` | Request 3DS |
| 3 | `:risk_level: = 'elevated'` | Review |
| 4 | Repeat failed CVC | Block (if enabled) |

Start with **Review** before **Block** to measure false positives.

## Verify Impact

After rule change, compare blocked payments in Dashboard → Payments (outcome: blocked).

`search_stripe_documentation` for latest Radar attribute names.

## Output Template

```
Radar Audit

Current rules: [summary from user screenshot or API if available]
Recommended additions:
1. [rule] — [rationale]

Rollout: Review → 7d → Block
```
