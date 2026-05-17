"""Notification channel and status enumerations."""

from enum import Enum


class NotificationChannel(str, Enum):
    EMAIL = "EMAIL"
    IN_APP = "IN_APP"


class NotificationStatus(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"


class NotificationType(str, Enum):
    # ── Legacy / manual ──────────────────────────────────────────────────────
    APPOINTMENT_REMINDER = "APPOINTMENT_REMINDER"       # generic (legacy)
    MANUAL_PATIENT = "MANUAL_PATIENT"
    MANUAL_ACCOUNT = "MANUAL_ACCOUNT"

    # ── Phase 5 — Appointment reminders (J-15, J-3, J-1) ────────────────────
    APPOINTMENT_REMINDER_15D = "APPOINTMENT_REMINDER_15D"   # 15 days before
    APPOINTMENT_REMINDER_3D = "APPOINTMENT_REMINDER_3D"     # 3 days before
    APPOINTMENT_REMINDER_1D = "APPOINTMENT_REMINDER_1D"     # 1 day before

    # ── Phase 5 — Terrain workflow ────────────────────────────────────────────
    TERRAIN_THANK_YOU = "TERRAIN_THANK_YOU"             # After on-site visit (→ Patient)

    # ── Phase 2 — Validation workflow (already used in code) ─────────────────
    LAB_DONE = "LAB_DONE"                               # MedicalProgram lab-validated (→ Clinic Doctor)
    CAMPAIGN_CLINIC_VALIDATED = "CAMPAIGN_CLINIC_VALIDATED"  # Clinic validated (→ Company Doctor)
    RESULTS_AVAILABLE = "RESULTS_AVAILABLE"             # Visit results ready (→ Patient)

    # ── Phase 5 — Certificate & program report ───────────────────────────────
    CERTIFICATE_AVAILABLE = "CERTIFICATE_AVAILABLE"     # Certificate generated (→ Patient)
    CAMPAIGN_REPORT = "CAMPAIGN_REPORT"                 # MedicalProgram finished report (→ Company Doctor)
