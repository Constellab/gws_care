"""DB migration v0.10.0 — New domain tables: PatientAccount, ExamTypeRef, ExamParameter,
CampaignExam, TubeQR, Prebilling, PrebillingLine, Invoice, CorrectionRequest, AuditLog.
Also adds medical workflow columns to CampaignPatient.
"""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.10.0",
    short_description="Add domain tables for full V2 workflows",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration100(BrickMigration):
    @classmethod
    def migrate(
        cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version
    ) -> None:
        db = sql_migrator.migrator.database

        from gws_care.audit.audit_log import AuditLog
        from gws_care.campaign.campaign_exam import CampaignExam
        from gws_care.correction.correction_request import CorrectionRequest
        from gws_care.exam_type_ref.exam_parameter import ExamParameter
        from gws_care.exam_type_ref.exam_type_ref import ExamTypeRef
        from gws_care.patient_account.patient_account import PatientAccount
        from gws_care.prebilling.prebilling import Invoice, Prebilling, PrebillingLine
        from gws_care.tube_qr.tube_qr import TubeQR

        db.create_tables(
            [
                PatientAccount,
                ExamTypeRef,
                ExamParameter,
                CampaignExam,
                TubeQR,
                Prebilling,
                PrebillingLine,
                Invoice,
                CorrectionRequest,
                AuditLog,
            ],
            safe=True,
        )

        # Add medical workflow columns to gws_care_campaign_patient (idempotent)
        db.execute_sql(
            "ALTER TABLE gws_care_campaign_patient "
            "ADD COLUMN IF NOT EXISTS medical_status VARCHAR(30) NOT NULL DEFAULT 'PENDING'"
        )
        db.execute_sql(
            "ALTER TABLE gws_care_campaign_patient "
            "ADD COLUMN IF NOT EXISTS psc_notes TEXT NULL DEFAULT NULL"
        )
        db.execute_sql(
            "ALTER TABLE gws_care_campaign_patient "
            "ADD COLUMN IF NOT EXISTS enterprise_notes TEXT NULL DEFAULT NULL"
        )
        db.execute_sql(
            "ALTER TABLE gws_care_campaign_patient "
            "ADD COLUMN IF NOT EXISTS patient_message TEXT NULL DEFAULT NULL"
        )
        db.execute_sql(
            "ALTER TABLE gws_care_campaign_patient "
            "ADD COLUMN IF NOT EXISTS psc_validated_at DATETIME NULL DEFAULT NULL"
        )
        db.execute_sql(
            "ALTER TABLE gws_care_campaign_patient "
            "ADD COLUMN IF NOT EXISTS enterprise_validated_at DATETIME NULL DEFAULT NULL"
        )
        db.execute_sql(
            "ALTER TABLE gws_care_campaign_patient "
            "ADD COLUMN IF NOT EXISTS published_at DATETIME NULL DEFAULT NULL"
        )
