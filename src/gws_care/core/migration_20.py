"""DB migration v0.29.0 — Baseline for merged Nour_app_dev branch.

This migration runs after all legacy migrations (0.1.0–0.10.9) and marks the
schema baseline for the combined Nour_app_dev branch. It also adds any columns
introduced by the main branch that are not yet in the production DB.
"""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.29.0",
    short_description="Main-branch baseline: add new columns from main-branch models",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration200(BrickMigration):
    @classmethod
    def migrate(
        cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version
    ) -> None:
        db = sql_migrator.migrator.database

        # ── gws_care_patient — new fields from main branch ───────────────────
        stmts = [
            "ALTER TABLE gws_care_patient ADD COLUMN IF NOT EXISTS sex VARCHAR(10) NULL DEFAULT NULL",
            "ALTER TABLE gws_care_patient ADD COLUMN IF NOT EXISTS nationality VARCHAR(100) NULL DEFAULT NULL",
            "ALTER TABLE gws_care_patient ADD COLUMN IF NOT EXISTS phone_country VARCHAR(10) NULL DEFAULT NULL",
            "ALTER TABLE gws_care_patient ADD COLUMN IF NOT EXISTS qr_code LONGTEXT NULL DEFAULT NULL",
            "ALTER TABLE gws_care_patient ADD COLUMN IF NOT EXISTS social_security_number VARCHAR(30) NULL DEFAULT NULL",
            "ALTER TABLE gws_care_patient ADD COLUMN IF NOT EXISTS weight DECIMAL(6,2) NULL DEFAULT NULL",
            "ALTER TABLE gws_care_patient ADD COLUMN IF NOT EXISTS height DECIMAL(5,2) NULL DEFAULT NULL",
            "ALTER TABLE gws_care_patient ADD COLUMN IF NOT EXISTS notification_preferences LONGTEXT NULL DEFAULT NULL",

            # ── gws_care_account — contact split + company_id ─────────────────
            "ALTER TABLE gws_care_account ADD COLUMN IF NOT EXISTS contact_first_name VARCHAR(150) NULL DEFAULT NULL",
            "ALTER TABLE gws_care_account ADD COLUMN IF NOT EXISTS contact_last_name VARCHAR(150) NULL DEFAULT NULL",

            # ── gws_care_patient_account — richer affiliation fields ───────────
            "ALTER TABLE gws_care_patient_account ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE'",
            "ALTER TABLE gws_care_patient_account ADD COLUMN IF NOT EXISTS start_date DATE NULL DEFAULT NULL",
            "ALTER TABLE gws_care_patient_account ADD COLUMN IF NOT EXISTS end_date DATE NULL DEFAULT NULL",
            "ALTER TABLE gws_care_patient_account ADD COLUMN IF NOT EXISTS employee_number VARCHAR(100) NULL DEFAULT NULL",
            "ALTER TABLE gws_care_patient_account ADD COLUMN IF NOT EXISTS position VARCHAR(200) NULL DEFAULT NULL",
            "ALTER TABLE gws_care_patient_account ADD COLUMN IF NOT EXISTS site VARCHAR(200) NULL DEFAULT NULL",
            "ALTER TABLE gws_care_patient_account ADD COLUMN IF NOT EXISTS department VARCHAR(200) NULL DEFAULT NULL",
            "ALTER TABLE gws_care_patient_account ADD COLUMN IF NOT EXISTS end_reason LONGTEXT NULL DEFAULT NULL",

            # ── gws_care_exam — new fields from main branch ───────────────────
            "ALTER TABLE gws_care_exam ADD COLUMN IF NOT EXISTS exam_type_ref_id VARCHAR(36) NULL DEFAULT NULL",
        ]

        # ── Create new tables from main branch (safe=True = IF NOT EXISTS) ────
        from gws_care.doctor.medical_doctor import MedicalDoctor
        from gws_care.exam.exam_type_model import ExamTypeModel
        from gws_care.patient.patient_doctor import PatientDoctor
        from gws_care.user.user_app_config import UserAppConfig
        from gws_care.visit.visit import Visit
        from gws_care.document_upload.document_text import DocumentText
        from gws_care.document_upload.uploaded_document import UploadedDocument
        from gws_care.role.user_care_role_account import UserCareRoleAccount
        from gws_care.campaign.campaign_exam_type import CampaignExamType

        db.create_tables([
            MedicalDoctor,
            ExamTypeModel,
            PatientDoctor,
            UserAppConfig,
            Visit,
            DocumentText,
            UploadedDocument,
            UserCareRoleAccount,
            CampaignExamType,
        ], safe=True)

        for stmt in stmts:
            db.execute_sql(stmt)
