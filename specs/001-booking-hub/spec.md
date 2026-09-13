# Feature Specification: Independent Gym Booking Hub

**Feature Branch**: `001-booking-hub`  
**Created**: 2026-09-13  
**Status**: Ready for planning  
**Input**: Independent app for gym users to log in, see reservations, and schedule next-week reservation attempts every Friday at 15:30, deployable on GitHub Pages.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Configure a weekly booking plan (Priority: P1)

A gym member creates one or more weekly reservation targets, choosing weekday, class time and the Friday launch time.

**Why this priority**: A clear plan is useful before any automation exists and is the core record a local agent will later execute.

**Independent Test**: A user adds, edits and removes plans on a phone; after reload, the visible agenda matches the saved plan.

**Acceptance Scenarios**:

1. **Given** a new user, **When** they add a Monday 18:00 class and choose Friday 15:30, **Then** the agenda shows the next Monday target and its Friday launch time.
2. **Given** an existing plan, **When** the user removes it, **Then** it disappears immediately and does not reappear after reload.

---

### User Story 2 - See confirmed and pending reservations (Priority: P1)

A user sees an understandable weekly agenda that differentiates configured targets, pending attempts, confirmed reservations and failures.

**Why this priority**: Users must be able to trust the app before they let a local agent act for them.

**Independent Test**: Given booking records in each state, a user can identify each status and its date/time without opening a detail screen.

**Acceptance Scenarios**:

1. **Given** a configured target without an outcome, **When** the agenda is opened, **Then** it is marked as planned rather than confirmed.
2. **Given** a confirmed record, **When** the agenda is opened, **Then** it shows the class date, time and confirmation state.

---

### User Story 3 - Connect a personal booking service (Priority: P2)

A user can connect their WodBuster account to a secure booking service that synchronises real reservations and launches due attempts without exposing credentials to the public site.

**Why this priority**: Browser-only GitHub Pages cannot run Friday tasks after the browser closes or send reliable booking notifications.

**Independent Test**: A user without a connection sees a clear offline state; a connected user sees the latest sync without revealing secrets.

**Acceptance Scenarios**:

1. **Given** no booking connection, **When** the user opens connection settings, **Then** the app explains that booking is not active.
2. **Given** a connected account, **When** the service reports a booking result, **Then** the agenda updates with the reported state and time.

---

### User Story 4 - Use it as a mobile app (Priority: P1)

A user installs the application on Android, opens a compact dashboard without unnecessary scrolling, and connects their booking account through a secure device-owned component.

**Why this priority**: The product is meant for a phone; credentials and scheduled execution must stay under the user's control on that phone.

**Independent Test**: A user installs the app, opens its home screen, and sees their upcoming targets and live reservations without a promotional hero or explanatory filler.

**Acceptance Scenarios**:

1. **Given** an installed app with two targets, **When** the user opens it, **Then** the account status, planned targets and live reservations are visible in the first phone screen where space permits.
2. **Given** a user connects WodBuster, **When** credentials are provided, **Then** they are sent over a secure connection and stored encrypted by the booking service, never by GitHub Pages.

### Edge Cases

- A Friday launch time occurs while the booking provider has not opened the next-week timetable.
- The agent is offline or the provider rejects a booking attempt.
- A user opens the public site from a new phone with no locally stored settings.
- A class is manually reserved outside the app and must be reconciled by the agent.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The app MUST let users create, edit and delete weekly booking targets with weekday, class time and launch time.
- **FR-002**: The default weekly launch time MUST be Friday at 15:30 and users MUST be able to change it.
- **FR-003**: The app MUST show each target's next intended class date and next launch time in Europe/Madrid time.
- **FR-004**: The app MUST distinguish planned, pending, confirmed and failed reservation states.
- **FR-005**: The public site MUST remain usable without a booking connection and MUST never persist booking-provider passwords locally.
- **FR-006**: The app MUST clearly show when no booking service is connected.
- **FR-007**: The booking service MUST be the only component allowed to execute booking attempts and retain encrypted provider credentials.
- **FR-008**: The app MUST make manual reservations reconcilable when the booking service reports them.
- **FR-009**: The project MUST be publishable as a static GitHub Pages site without personal network addresses or secrets.
- **FR-010**: The mobile home screen MUST prioritise account state, planned targets and live reservations over decorative headings or explanatory sections.
- **FR-011**: The installed Android application MUST never retain booking credentials; the booking service MUST store them encrypted and never return them to the client.
- **FR-012**: The service MUST evaluate due Friday launch times in Europe/Madrid and must not drift during daylight-saving transitions.
- **FR-013**: The service MUST notify the subscribed mobile device after each settled reservation attempt.

### Key Entities

- **Booking target**: Recurring class intention with weekday, class time and launch time.
- **Reservation outcome**: A dated state reported for a target, including planned, pending, confirmed or failed.
- **Booking service**: Backend component that stores encrypted provider credentials, executes schedules and reports outcomes.
- **Push subscription**: Device-specific, revocable address used to notify a user after a booking result.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new user can create a weekly booking plan with two classes in under 90 seconds on a phone.
- **SC-002**: Users can identify the state and date of every next-week target without leaving the agenda screen.
- **SC-003**: Reloading the site preserves 100% of plans created on the same device until the user removes them.
- **SC-004**: The published static site contains no user credentials, booking-provider tokens or personal infrastructure addresses.
- **SC-005**: When an agent is connected, its latest reported booking outcome is shown to the user within one refresh of the agenda.

## Assumptions

- WodBuster remains the first supported booking provider, but the public app does not present itself as an official WodBuster product.
- The first public release is Spanish and mobile-first.
- A shared booking backend will be hosted separately from GitHub Pages before real accounts are enabled.
- GitHub Pages hosts only static assets; scheduled booking execution and Web Push happen in the backend.
