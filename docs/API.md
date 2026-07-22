# API Reference

Base URL: `http://127.0.0.1:5000`. All endpoints are under `/api`.
Auth: `Authorization: Bearer <token>` + `X-Workspace-Id: <id>` for scoped routes.

## Auth
| Method | Route | Permission |
| --- | --- | --- |
| POST | `/api/auth/register` | Public |
| POST | `/api/auth/login` | Public |
| POST | `/api/auth/logout` | Authenticated |
| GET | `/api/auth/profile` | Authenticated |
| PUT | `/api/auth/profile` | Authenticated |

## Workspaces & members
| Method | Route | Permission |
| --- | --- | --- |
| GET | `/api/workspaces` | Authenticated |
| POST | `/api/workspaces` | Authenticated |
| GET | `/api/workspaces/:id` | Member |
| PUT | `/api/workspaces/:id` | Owner |
| GET | `/api/workspaces/:id/members` | Member |
| POST | `/api/workspaces/:id/members` | Owner |
| PUT | `/api/workspaces/:id/members/:memberId` | Owner |
| DELETE | `/api/workspaces/:id/members/:memberId` | Owner |

## Social accounts
| Method | Route | Permission |
| --- | --- | --- |
| GET | `/api/social-accounts` | Member |
| POST | `/api/social-accounts/connect/youtube` | Editor, Owner |
| POST | `/api/social-accounts/connect/:platform` | Editor, Owner |
| GET | `/api/social-accounts/:id` | Member |
| GET | `/api/social-accounts/:id/history?range=7d\|30d\|90d\|all` | Member |
| GET | `/api/social-accounts/:id/grade` | Member |
| DELETE | `/api/social-accounts/:id` | Editor, Owner |
| GET | `/api/social-accounts/export?format=csv\|pdf` | Owner (Pro/Agency) |

## AI generation
| Method | Route | Permission |
| --- | --- | --- |
| POST | `/api/generate/caption` | Editor, Owner |
| POST | `/api/generate/hashtags` | Editor, Owner |
| POST | `/api/generate/content-idea` | Editor, Owner |
| POST | `/api/generate/viral-score` | Editor, Owner |
| POST | `/api/generate/sentiment` | Editor, Owner |
| GET | `/api/ai-generations` | Member |
| GET | `/api/ai-generations/:id` | Member |
| DELETE | `/api/ai-generations/:id` | Editor, Owner |
| GET | `/api/credit-usage/current` | Member |

## Scheduled posts
| Method | Route | Permission |
| --- | --- | --- |
| POST | `/api/scheduled-posts` | Editor, Owner |
| GET | `/api/scheduled-posts` | Member |
| GET | `/api/scheduled-posts/:id` | Member |
| PUT | `/api/scheduled-posts/:id` | Editor, Owner |
| PATCH | `/api/scheduled-posts/:id/cancel` | Editor, Owner |

## Billing
| Method | Route | Permission |
| --- | --- | --- |
| GET | `/api/billing/plans` | Public |
| POST | `/api/billing/checkout` | Owner |
| POST | `/api/billing/webhook/stripe` | Stripe signature |
| POST | `/api/billing/webhook/razorpay` | Razorpay signature |
| GET | `/api/billing/subscription` | Owner |
| POST | `/api/billing/cancel` | Owner |

## Media kit, admin, dashboard, misc
| Method | Route | Permission |
| --- | --- | --- |
| GET | `/api/media-kit/:slug` | Public |
| PUT | `/api/media-kit` | Owner, Editor |
| GET | `/api/platform-admin/workspaces` | Platform admin |
| GET | `/api/platform-admin/workspaces/:id` | Platform admin |
| PATCH | `/api/platform-admin/workspaces/:id/plan` | Platform admin |
| GET | `/api/me/dashboard` | Member |
| GET | `/api/notifications` | Member |
| PATCH | `/api/notifications/:id/read` | Member |
| PATCH | `/api/notifications/read-all` | Member |
| POST | `/api/referrals` | Authenticated |
| GET | `/api/referrals` | Authenticated |
