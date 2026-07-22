# Role Permissions

| Module | Viewer | Editor | Owner | Platform Admin |
| --- | :---: | :---: | :---: | :---: |
| View dashboard / accounts / history | ✅ | ✅ | ✅ | ✅ (all) |
| Connect / disconnect social accounts | ❌ | ✅ | ✅ | ❌ |
| Generate AI content | ❌ | ✅ | ✅ | ❌ |
| Schedule / cancel posts | ❌ | ✅ | ✅ | ❌ |
| Edit media kit / branding | ❌ | ✅ | ✅ | ❌ |
| Invite / remove team members | ❌ | ❌ | ✅ | ❌ |
| Billing (checkout, cancel) | ❌ | ❌ | ✅ | ❌ |
| Export CSV / PDF (Pro/Agency) | ✅ | ✅ | ✅ | ✅ (all) |
| Manage platform-wide plans | ❌ | ❌ | ❌ | ✅ |

Webhook endpoints (`/api/billing/webhook/*`) are authenticated by provider
signature verification, not user roles.
