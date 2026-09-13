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

### User Story 3 - Connect a personal booking agent (Priority: P2)

A user can connect their own local booking agent to synchronise real reservation outcomes and activate scheduled attempts without exposing credentials to the public site.

**Why this priority**: Browser-only GitHub Pages cannot keep credentials or run Friday tasks after the browser closes.

**Independent Test**: A user without an agent sees a clear offline state; a user with an authorised agent sees its connection and most recent sync without revealing secrets.

**Acceptance Scenarios**:

1. **Given** no agent is connected, **When** the user opens connection settings, **Then** the app explains that booking is not active and does not ask for their WodBuster password.
2. **Given** a connected agent, **When** it reports a booking result, **Then** the agenda updates with the reported state and time.

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
- **FR-005**: The public site MUST remain usable without credentials and MUST not request or persist booking-provider passwords.
- **FR-006**: The app MUST clearly show when no personal booking agent is connected.
- **FR-007**: A connected agent MUST be the only component allowed to execute booking attempts or retain provider credentials.
- **FR-008**: The app MUST make manual reservations reconcilable when the connected agent reports them.
- **FR-009**: The project MUST be publishable as a static GitHub Pages site without personal network addresses or secrets.

### Key Entities

- **Booking target**: Recurring class intention with weekday, class time and launch time.
- **Reservation outcome**: A dated state reported for a target, including planned, pending, confirmed or failed.
- **Personal agent**: User-owned local component that securely connects to the booking provider and reports outcomes.

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
- Each person runs or authorises their own local agent; there is no shared central account service in the first release.
- GitHub Pages hosts only static assets; scheduled booking execution is intentionally deferred to the user-owned agent.

