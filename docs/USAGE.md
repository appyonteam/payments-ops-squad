# Usage

Command names below are for a plugin install. With the install script, drop the `payments-ops-squad:` prefix (for example
`/pay-export`). You can also ask in plain language; Claude picks the matching skill or specialist from its description.

Every answer ends with **Facts / Hypotheses / Sources (with date)**. Changes to production are only ever proposed as
recommendations for a human to approve.

## /payments-ops-squad:pay-export

Analyze a Stripe, Primer or FunnelFox export. Arguments: `<file(s)> [question]`.

```text
/payments-ops-squad:pay-export exports/payments-part1.csv exports/payments-part2.csv Approval by card brand, per customer and per attempt
```

Detects the origin from the header and the id format, deduplicates, checks daily coverage per status before any rate, and prints
numerator, denominator, grain, period and timezone for every rate.

## /payments-ops-squad:pay-incident

Investigate a payments incident. Arguments: `<symptom and time window>`.

```text
/payments-ops-squad:pay-incident Since yesterday morning, renewals on one processor started failing. What changed?
```

Confirms the symptom against a baseline, builds the change timeline, isolates the failing layer and ranks hypotheses with the
check that would confirm or reject each one.

## /payments-ops-squad:pay-decline

Explain a decline or error code. Arguments: `<code> [vendor] [context]`.

```text
/payments-ops-squad:pay-decline insufficient_funds Stripe, first payment, no 3DS
```

Names the code namespace, paraphrases the official meaning with URL and date, and reports what the source says about soft or
hard, retrying and the customer message.

## /payments-ops-squad:pay-workflow

Review a workflow or rule set. Arguments: `<file or description> [goal]`.

```text
/payments-ops-squad:pay-workflow workflow-export.json Fewer declines on renewals without more disputes
```

Maps the flow, checks each rule (fallback on hard declines, retries stacked across layers, loops, unnecessary 3DS, recurring
charges sent as merchant-initiated) and proposes changes with a backtest and rollback plan.

## /payments-ops-squad:pay-ask

Ask a general payments operations question. Arguments: `<question>`.

```text
/payments-ops-squad:pay-ask If FunnelFox, Primer and Stripe Billing can all retry a renewal, how do I find out which one is retrying?
```

Routes the question to the right skill or specialist and answers per layer, with sources and dates.

## /payments-ops-squad:pay-docs

Fetch an official documentation page into the local cache. Arguments: `<docs URL>` or `--index stripe|primer|funnelfox`, with
optional `--refresh` and `--max-age-days N`.

```text
/payments-ops-squad:pay-docs https://docs.stripe.com/declines/codes
/payments-ops-squad:pay-docs --index funnelfox
```

Only `https://docs.stripe.com/`, `https://primer.io/docs/` and `https://funnelfox.com/docs/` are accepted. The first output line is
the cache file; cite its `source_url` and `fetched_at`.

## Using the specialists directly

In Claude Code you can ask for a specialist by name, for example: "Use primer-3ds to separate authentication failures from
authorization failures in this export" or "Use funnelfox-retries to check whether retries are stacked across layers". For complex
Primer investigations start with `primer-squad`; for FunnelFox start with the `funnelfox-core` skill; for Stripe account questions
start with the `stripe-router` skill, which names the owning agent (`stripe-payments`, `stripe-risk`, `stripe-disputes`,
`stripe-billing` or `stripe-finance`). You can also ask for one of them directly, for example: "Use stripe-billing to explain why
MRR dropped".
