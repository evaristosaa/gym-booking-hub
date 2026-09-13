# Tasks: Hosted booking and mobile notifications

## Dependencies

`US1 agenda` → `US2 live reservations` → `US3 secure connection/scheduler` → `US4 mobile installation/push`.

## Phase 1 — Foundation

- [ ] T001 Add backend runtime and container configuration in `backend/`
- [ ] T002 Add backend environment contract and secret exclusions in `backend/.env.example` and `.gitignore`
- [ ] T003 Add API authentication model and migration in `backend/`

## Phase 2 — Agenda (US1)

- [ ] T004 [US1] Replace browser-only targets with authenticated schedule API calls in `public/app.js`
- [ ] T005 [US1] Add schedule create/edit/delete screens in `public/index.html`
- [ ] T006 [US1] Add schedule API integration tests in `backend/tests/`

## Phase 3 — Live reservations (US2)

- [ ] T007 [US2] Add future reservation query and state model in `backend/`
- [ ] T008 [US2] Render real confirmed/pending/failed future reservations in `public/app.js`
- [ ] T009 [US2] Add reconciliation of manual provider reservations in `backend/`

## Phase 4 — Connection and scheduling (US3)

- [ ] T010 [US3] Implement encrypted WodBuster credential vault in `backend/`
- [ ] T011 [US3] Adapt provider verification and booking client from the existing WodBooker behaviour in `backend/`
- [ ] T012 [US3] Implement Europe/Madrid due-schedule worker and atomic attempt claiming in `backend/`
- [ ] T013 [US3] Add safe error reporting and booking audit tests in `backend/tests/`

## Phase 5 — Installed mobile app and push (US4)

- [ ] T014 [US4] Request push permission and register subscription in `public/app.js`
- [ ] T015 [US4] Add VAPID/Web Push sender and retry policy in `backend/`
- [ ] T016 [US4] Verify notification delivery from a settled reservation outcome on Android Chrome

## Phase 6 — Deployment and review

- [ ] T017 Add backend deployment guide and security checklist in `docs/`
- [ ] T018 Deploy backend only after owner approves hosting and cost
- [ ] T019 Publish static PWA to GitHub Pages after backend API URL is configured

