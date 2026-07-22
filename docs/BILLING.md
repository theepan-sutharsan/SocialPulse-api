# Billing

Two providers are supported: **Stripe** (USD) and **Razorpay** (INR).

## Plans

| Tier | Credits/mo | USD | INR |
| --- | --- | --- | --- |
| free | 5 | 0 | 0 |
| pro | 500 | 19 | 1499 |
| agency | 2000 | 79 | 6499 |

(See `Config.PLAN_CREDITS`, `PLAN_PRICES_USD`, `PLAN_PRICES_INR`.)

## Checkout

`POST /api/billing/checkout {plan_tier, provider}` (owner only) returns a
`checkout_url`. When provider keys are configured a real Checkout Session /
Order is created; otherwise a **simulated** checkout applies the upgrade
immediately so the flow is demoable locally.

## Webhooks

`POST /api/billing/webhook/stripe` and `/razorpay` verify the provider signature
before mutating subscription state. On activation the plan tier + credit
allotment are updated; on cancellation the workspace reverts to `free`.
