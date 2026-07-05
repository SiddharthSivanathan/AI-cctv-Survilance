# ADR 0009 — Notifications & Reports (V1)

- **Status:** Accepted
- **Date:** 2026-07-05
- **Phase:** 10 (Reports & Notifications)

## Context
V1 needs to notify humans and produce business reports. Product direction:
in-app + email + browser notifications only (no SMS/Slack/etc.), deterministic
(non-LLM) report narratives, and PDF/CSV export.

## Pre-existing WIP resolution
Phase 10 was partially started (uncommitted): `Notification` model,
`notification_setting` model, `notification_repository`, and report/notification
schemas. Decision:
- **Kept:** `Notification` model (per-user targeting is better than a shared
  read-state), `NotificationRepository`, report + notification schemas.
- **Removed:** `notification_setting` model + repository — it **duplicated**
  `Organization.alert_email_enabled` and lacked RLS (every other tenant table is
  RLS-protected). Consolidated preferences onto `Organization`
  (`notify_critical_only`, `daily_summary_email`) — single source of truth,
  RLS-consistent.

## Decisions
1. **Notifications = In-app + Email + Browser.** In-app notifications are written
   in the **same transaction** as the alert. Email is sent **async via Celery**
   (the API enqueues a fully-formed job after commit; the worker is a dumb SMTP
   sender that logs when SMTP is unconfigured). Browser notifications use the
   Notifications API, only while the tab is visible and permission is granted.
   All notifications fire **only after the event is committed**.
2. **Email gating:** immediate email for camera-offline / billing-unattended /
   queue-exceeded / occupancy-exceeded, gated by `alert_email_enabled` +
   `notify_critical_only`; recipient is the org contact email.
3. **Reports** are generated deterministically (facts-only executive summary +
   rule-based recommendations — no LLM in V1, reserved for V2). Aggregates come
   from `camera_metrics` + `camera_events` (never raw telemetry). Outputs:
   in-app view, **PDF** (reportlab: branding, logo, page numbers, timestamp), and
   **CSV** (metrics + tables only). On-demand generation + Beat-scheduled
   generation (daily/weekly/monthly); reports are **not** auto-emailed.
4. **`camera_metrics`-based** report data (part of Phase 9) means reports need no
   new telemetry.

## Deferred (V2)
LLM narratives, SMS/Slack/Teams/WhatsApp/push, per-user notification routing,
scheduled report emails.
