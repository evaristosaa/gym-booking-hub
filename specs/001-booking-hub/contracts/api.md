# API Contract (v1)

All endpoints are HTTPS. A user session is required except account-start endpoints. Responses must never include provider passwords, session cookies or encrypted credential blobs.

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/v1/auth/start` | Start user login/registration flow. |
| `POST` | `/v1/connections/wodbuster` | Verify and save an encrypted WodBuster connection. |
| `GET` | `/v1/connections/wodbuster` | Read masked connection status only. |
| `GET, POST` | `/v1/schedules` | List and create weekly targets. |
| `PATCH, DELETE` | `/v1/schedules/{id}` | Change or disable a target. |
| `GET` | `/v1/reservations?future=true` | Return reservations whose class time has not passed. |
| `POST` | `/v1/push-subscriptions` | Register a device push subscription. |
| `DELETE` | `/v1/push-subscriptions/{id}` | Revoke a device subscription. |

The internal worker endpoint is never public. It claims due schedules atomically, executes provider attempts, stores only safe diagnostic text, then enqueues push notifications.

