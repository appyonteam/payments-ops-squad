# Third-party notices

This file lists third-party material included in or referenced by payments-ops-squad, with its license.

## Included: Stripe skills adapted from appeeky/stripe-skills

- Source: https://github.com/appeeky/stripe-skills (commit 2b5d841, 2026-07-19)
- License: MIT, Copyright (c) 2026 Erencan
- Location in this repository: `skills/stripe/`
- Changes from upstream:
  - each `SKILL.md` carries an attribution line after its frontmatter;
  - `stripe-security-audit` was reworded so that it no longer spells out a secret key prefix literally;
  - `stripe-router` invokes the target skill by name instead of reading `skills/<skill-name>/SKILL.md` from a path, and its
    description no longer lists the `/stripe-skill` and `/stripe` triggers (it lists `/payments-ops-squad:pay-ask`);
  - `stripe-billing-context` carries a note that the file it writes holds account details and must stay out of version
    control;
  - `cohort-retention` uses a `YYYY-MM` placeholder instead of a fixed month in its output template;
  - `stripe-router` has an added "Agent" column in its routing table naming the specialist agent that owns each skill (v0.2.0);
  - `stripe-router` has a routing row for Early Fraud Warning with no skill (forwarded to `stripe-disputes`), a note on webhook
    ownership, and a corrected "How is the business doing?" chain row (v0.2.0).

  Content is otherwise unchanged.

Skills included (35):

- `active-subscriptions-audit`
- `card-funding-risk`
- `checkout-conversion`
- `checkout-implementation`
- `churn-analysis`
- `cohort-retention`
- `coupon-promotion-audit`
- `customer-360`
- `customer-portal-setup`
- `customer-segmentation`
- `dispute-refund-audit`
- `email-dunning-setup`
- `financial-reconciliation`
- `invoice-revenue-audit`
- `mrr-arr-snapshot`
- `past-due-dunning`
- `payment-failure-audit`
- `payout-balance-report`
- `pricing-experiments`
- `pricing-products-audit`
- `radar-fraud-rules`
- `revenue-forecasting`
- `revenue-recognition`
- `stripe-billing-context`
- `stripe-connect`
- `stripe-health-dashboard`
- `stripe-integration-review`
- `stripe-router`
- `stripe-security-audit`
- `subscription-plan-changes`
- `tax-compliance`
- `upsell-expansion`
- `usage-based-billing`
- `webhook-implementation`
- `webhook-reliability`

License text (reproduced in full, as required by the MIT License):

```text
MIT License

Copyright (c) 2026 Erencan

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Not redistributed (fetched from official sources on demand)

The following material is never versioned in this repository nor included in the release packages. Documentation pages are
fetched on demand by `tools/fetch_doc.py` (or the `pay-docs` command) from the official source into the user's local
knowledge cache, under the terms that apply to each source. The public repositories are listed for reference only and are not
downloaded automatically. Agents and skills cite the official URL instead of copying vendor text. See `knowledge/sources.json`.

| Material | Official source | License |
|---|---|---|
| Stripe documentation | https://docs.stripe.com | Stripe terms; not redistributed |
| Primer documentation | https://primer.io/docs | Primer terms; not redistributed |
| FunnelFox documentation | https://funnelfox.com/docs | No redistribution license; not redistributed |
| primer-io/primer-sdk-ios | https://github.com/primer-io/primer-sdk-ios | MIT |
| primer-io/primer-sdk-3ds-ios | https://github.com/primer-io/primer-sdk-3ds-ios | MIT; contains a third-party Netcetera binary that is not covered by the MIT License |
| primer-io/sdk-android | https://github.com/primer-io/sdk-android | BSD-3-Clause |
| primer-io/example-web-checkout | https://github.com/primer-io/example-web-checkout | No license (archived repository); not redistributed |
| adaptyteam/funnelfox-billing-js | https://github.com/adaptyteam/funnelfox-billing-js | MIT, Copyright (c) 2024 Funnelfox |

Stripe, Primer and FunnelFox are trademarks of their respective owners. This is an independent project, not affiliated
with, endorsed by or sponsored by Stripe, Primer or FunnelFox.
