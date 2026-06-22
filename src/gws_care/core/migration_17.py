"""DB migration v0.10.7 — Create all tables missing from previous migrations."""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.10.7",
    short_description="Create missing tables: consultation, prescriptions, notifications, billing, scheduling, etc.",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration107(BrickMigration):
    @classmethod
    def migrate(
        cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version
    ) -> None:
        from gws_care.billing.price_list import PriceList
        from gws_care.company.company import Company
        from gws_care.consultation.consultation import Consultation
        from gws_care.dashboard.dashboard_snapshot import DashboardSnapshot
        from gws_care.exam.exam_file import ExamFile
        from gws_care.exam.exam_parameter_result import ExamParameterResult
        from gws_care.messaging.patient_message import PatientMessage
        from gws_care.notification.notification_models import (
            BrevoConfig,
            NotificationBell,
            NotificationLog,
            NotificationPreference,
            SmtpConfig,
        )
        from gws_care.patient.patient_consent import PatientConsent
        from gws_care.patient.patient_deletion_log import PatientDeletionLog
        from gws_care.patient.patient_document import PatientDocument
        from gws_care.patient.patient_note import PatientNote
        from gws_care.prescription.prescription import Prescription, PrescriptionLine
        from gws_care.billing.patient_invoice import PatientInvoice, PatientInvoiceLine
        from gws_care.scheduling.doctor_schedule import DoctorSchedule, DoctorUnavailableDay
        from gws_care.user.user_language_pref import UserLanguagePref

        db = sql_migrator.migrator.database

        # Pass 1: tables with no FK dependencies on newly-created tables
        db.create_tables([
            UserLanguagePref,
            PatientDeletionLog,
            DashboardSnapshot,
            SmtpConfig,
            BrevoConfig,
            Company,
            Consultation,
            ExamFile,
            ExamParameterResult,
            PatientConsent,
            PatientMessage,
            PatientDocument,
            PatientNote,
            DoctorSchedule,
            DoctorUnavailableDay,
            PriceList,
            NotificationPreference,
            NotificationLog,
        ], safe=True)

        # Pass 2: tables that depend on Pass 1
        db.create_tables([
            Prescription,
            NotificationBell,
        ], safe=True)

        # Pass 3: tables that depend on Pass 2
        db.create_tables([
            PrescriptionLine,
            PatientInvoice,
        ], safe=True)

        # Pass 4: tables that depend on Pass 3
        db.create_tables([
            PatientInvoiceLine,
        ], safe=True)
