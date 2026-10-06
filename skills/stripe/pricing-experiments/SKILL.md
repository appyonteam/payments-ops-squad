---
name: pricing-experiments
description: "Designs Stripe pricing A/B tests, price increases, grandfathering, and elasticity analysis. Use when the user mentions \"price test\", \"raise prices\", \"pricing experiment\", \"grandfathering\", \"price elasticity\", or \"should we change pricing\". For catalog audit, see pricing-products-audit."
metadata:
  version: 1.0.0
---

> Adapted by Vitor Dvorschi (Appyon) from [appeeky/stripe-skills](https://github.com/appeeky/stripe-skills) (MIT License, (c) 2026 Erencan).

# Pricing Experiments

## Stripe MCP Setup

Requires **Stripe MCP** (https://docs.stripe.com/mcp). `GetMcpTools` before `CallMcpTool`. Paginate all lists (`limit: 100`, `starting_after` while `has_more`). Amounts in **cents**. Read-only for audits; confirm before writes.

## Workflow

1. Baseline: current prices + subs per price (`pricing-products-audit`)
2. Design test:
   - New `Price` object (never edit existing -- create new)
   - Split traffic at checkout (price ID by cohort/flag)
   - Grandfather existing subs (leave on old price)
3. Metrics to compare: conversion %, ARPU, churn at 30/60d

## Price Increase Playbook

| Step | Action |
|------|--------|
| 1 | Create new higher price |
| 2 | New customers -> new price |
| 3 | Existing -> keep or migrate with notice (email + `subscriptions.update`) |
| 4 | Measure churn delta post-migration |

## Output Template

```
Pricing Test Plan

Hypothesis: [raising X->Y increases ARPU without >Zpp churn]
Variants: control [price_A] vs test [price_B]
Sample size needed: [N per arm]
Success metric: ARPU / conversion / 30d retention
Grandfathering: [policy]
```

Never mutate a live `Price` -- always create a new one.
