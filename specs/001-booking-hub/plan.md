# Implementation Plan: Hosted booking and mobile notifications

**Branch**: `main` · **Spec**: [spec.md](spec.md) · **Date**: 2026-09-13

## Technical Context

- **Public client**: static PWA on GitHub Pages.
- **Booking backend**: containerised Python service with a separate worker process and PostgreSQL.
- **Provider**: WodBuster integration adapted from the proven WodBooker behaviour, but with clean multi-user boundaries.
- **Scheduler**: runs every minute; each due launch is calculated in `Europe/Madrid`, avoiding fixed UTC/DST mistakes.
- **Notifications**: Web Push to the PWA service worker; permission is explicit and subscriptions are revocable.
- **Authentication**: account session handled by the backend; booking credentials are encrypted at rest with a deployment secret/KMS and never returned by API responses.

## Constitution Check

| Principle | Result | Rationale |
|---|---|---|
| Credentials never leave user control | Pass with condition | They leave the browser only over HTTPS and stay encrypted in the booking backend; no public static asset contains them. |
| Pages is presentation | Pass | GitHub Pages is static only; it cannot schedule or access provider credentials. |
| No fake confirmations | Pass | A reservation is displayed as confirmed only after the provider response is persisted. |
| Mobile first | Pass | PWA and push flow target Android Chrome. |
| Portable by default | Pass | Frontend is static; backend is containerised and documented. |

## Research Decisions

### Schedule handling

**Decision**: run a worker every minute and compare plan times in `Europe/Madrid`.

**Rationale**: Cloudflare Cron uses UTC, so a fixed Friday 15:30 expression would shift one hour across daylight-saving changes.

**Alternative rejected**: fixed UTC cron expression.

### Notification delivery

**Decision**: Web Push through the installed PWA service worker.

**Rationale**: Android Chrome can wake the service worker and display a notification even when the app page is closed, after explicit permission.

**Alternative rejected**: browser tab notification; it dies with the tab.

### Hosting boundary

**Decision**: GitHub Pages for client; separate HTTPS backend plus worker for secrets and scheduling.

**Rationale**: Pages cannot securely persist per-user credentials or execute scheduled work.

**Alternative rejected**: save credentials in browser storage or GitHub repository secrets.

## Project Structure

```text
public/                 PWA client, GitHub Pages
backend/                API and scheduled worker (to implement)
specs/001-booking-hub/  contracts and delivery plan
```

## Delivery Stages

1. Finish compact PWA: agenda, connection state and live reservations panel.
2. Create backend authentication, encrypted credential vault and provider verification.
3. Add schedules, due worker, provider outcomes and reconciliation.
4. Add PWA push subscription and result notifications.
5. Deploy backend only after security review, then publish Pages.

