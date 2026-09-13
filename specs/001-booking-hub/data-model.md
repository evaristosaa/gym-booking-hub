# Data Model

## User

- `id`, `email`, `created_at`, `status`
- Owns booking connections, schedules, reservation outcomes and push subscriptions.

## Booking Connection

- `id`, `user_id`, `provider`, `box_url`, `credential_ciphertext`, `credential_key_version`, `verified_at`, `status`
- Credentials are write-only: neither API nor logs ever return the plaintext.

## Weekly Schedule

- `id`, `user_id`, `connection_id`, `weekday`, `class_time`, `launch_weekday`, `launch_time`, `timezone`, `enabled`
- Defaults: Friday 15:30, Europe/Madrid.

## Reservation Attempt

- `id`, `schedule_id`, `target_date`, `state`, `started_at`, `settled_at`, `provider_reference`, `safe_error`
- States: `planned → pending → confirmed | failed | cancelled`.

## Push Subscription

- `id`, `user_id`, `endpoint`, `public_key`, `auth_secret`, `created_at`, `revoked_at`
- One user may have several devices. Failed deliveries revoke only that subscription.

