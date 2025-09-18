# Database Schema Documentation

## Core Entities

### Users & Roles
`users` stores authentication profiles with role assignments (`requester`, `manager`, `fleet_admin`, `driver`, `auditor`), activity flags, optional department, and 2FA status. Relationships connect users to booking requests, approvals, driver profiles, assignments, audit logs, and notification preferences.【F:backend/app/models/user.py†L11-L59】

### Vehicles & Drivers
- `vehicles` tracks fleet assets, including registration, make/model, capacity, fuel type, status, mileage, and compliance documents with expiry dates and storage paths.【F:backend/app/models/vehicle.py†L1-L64】
- `drivers` maintains company driver records, linking optionally to a user account, licensing information, status, and availability schedules stored as JSON for weekly calendars.【F:backend/app/models/driver.py†L1-L48】

### Booking Workflow
- `booking_requests` records trip purpose, passenger counts, pickup/drop-off details, preferred vehicle class, workflow status, and timestamps. Each booking references the requester and has optional assignment/job run relations.【F:backend/app/models/booking.py†L1-L64】
- `approvals` captures multi-level managerial decisions, including delegation, reasons, and timestamps. `approval_delegations` lets managers grant temporary authority to other users.【F:backend/app/models/approval.py†L19-L91】
- `assignments` joins bookings with specific vehicles and drivers once approved, preserving the assigning user, notes, and history entries for allocation changes.【F:backend/app/models/assignment.py†L1-L44】
- `job_runs` log operational execution: check-in/out data (datetime, mileage, geotagged images), expense tracking with review workflow, incident reports, and final status. Relationships allow expense reviewers to be audited.【F:backend/app/models/job_run.py†L1-L72】

### Scheduling & Availability
`resource_calendar_events` stores manual blocks, maintenance windows, or custom events against vehicles or drivers, enabling conflict detection alongside the automated booking calendar.【F:backend/app/models/calendar_event.py†L15-L68】 Driver availability schedules are held in the `drivers` JSON column, while fleet-level working hours and holidays live in administrative tables described below.

### Notifications & Auditability
- `notifications` persist in-app messages per user with categories, metadata payloads, read status, and delivery channel tracking. `notification_preferences` records per-user channel toggles (in-app, email, LINE) and access tokens.【F:backend/app/models/notification.py†L1-L48】
- `audit_logs` centralise user actions with associated HTTP status codes, IP addresses, and contextual metadata for compliance reporting.【F:backend/app/models/system.py†L108-L141】

### System Administration
`system_configurations` acts as a singleton row for global policies (maintenance mode, booking limits, working day windows, escalation thresholds). It owns related collections: `system_holidays` (corporate shutdown days) and `system_working_hours` (per-weekday operating windows). Health checks and monitoring metrics persist in `system_health_records`.【F:backend/app/models/system.py†L14-L140】

## Relationships at a Glance
- **User ↔ BookingRequest:** one-to-many via `requester_id`.
- **BookingRequest ↔ Approval:** one-to-many for staged approvals; cascades on delete to keep workflow consistent.【F:backend/app/models/booking.py†L37-L51】【F:backend/app/models/approval.py†L31-L59】
- **BookingRequest ↔ Assignment ↔ Vehicle/Driver:** assignment ensures exclusivity by referencing each entity once per confirmed booking.【F:backend/app/models/assignment.py†L15-L41】
- **BookingRequest ↔ JobRun:** one-to-one capturing execution outcomes and expenses.【F:backend/app/models/job_run.py†L19-L69】
- **User ↔ Driver:** optional one-to-one linking employee accounts with driver records.【F:backend/app/models/user.py†L35-L59】【F:backend/app/models/driver.py†L19-L38】
- **SystemConfiguration ↔ Holidays/WorkingHours:** cascade updates to enforce consistent operating calendars.【F:backend/app/models/system.py†L60-L105】

## Extension Points
- Use Alembic migrations for schema evolution; metadata is centralised under `app.models.Base` for autogeneration.【F:backend/alembic/env.py†L12-L104】
- New modules can attach to existing relationships (e.g., additional notification channels or analytics tables) by importing the shared Base and referencing foreign keys appropriately.
