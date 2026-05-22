import reflex as rx
from gws_reflex_main import ReflexMainState, main_component, register_gws_reflex_app

from .account_detail.account_detail_component import account_detail_page
from .account_detail.account_detail_state import AccountDetailState
from .account_list.account_list_component import account_list_page
from .account_list.account_list_state import AccountListState
from .admin.admin_component import settings_page
from .admin.admin_state import AdminState
from .admin.general_settings_state import GeneralSettingsState
from .campaign_detail.campaign_detail_component import campaign_detail_page
from .campaign_detail.campaign_detail_state import CampaignDetailState
from .campaign_list.campaign_list_component import campaign_list_page
from .campaign_list.campaign_list_state import CampaignListState
from .certificate_detail.certificate_detail_component import certificate_detail_page
from .certificate_detail.certificate_detail_state import CertificateDetailState
from .common.language_state import LanguageState
from .common.page_layout import page_layout
from .consultation_detail.consultation_detail_component import consultation_detail_page
from .consultation_detail.consultation_detail_state import ConsultationDetailState
from .dashboard.dashboard_component import dashboard_page
from .dashboard.dashboard_state import DashboardState
from .exam_detail.exam_detail_component import exam_detail_page
from .exam_detail.exam_detail_state import ExamDetailState
from .notifications.notifications_component import notifications_page
from .notifications.notifications_state import NotificationsState
from .patient_detail.patient_detail_component import patient_detail_page
from .patient_detail.patient_detail_state import PatientDetailState
from .patient_list.patient_list_component import patient_list_page
from .patient_list.patient_list_state import PatientListState
from .patient_portal.patient_portal_component import (
    my_appointments_page,
    my_documents_page,
    my_messages_page,
    my_results_page,
)
from .patient_portal.patient_portal_state import PatientPortalState
from .prescription_detail.prescription_detail_component import prescription_detail_page
from .prescription_detail.prescription_detail_state import PrescriptionDetailState
from .switch_role.switch_role_component import switch_role_page
from .switch_role.switch_role_state import SwitchRoleState
from .terrain.terrain_component import terrain_page
from .terrain.terrain_state import TerrainState
from .visit_detail.visit_detail_component import visit_detail_page
from .visit_detail.visit_detail_state import VisitDetailState
from .visit_list.visit_list_component import visit_list_page
from .visit_list.visit_list_state import VisitListState


def _ensure_care_db_tables() -> None:
    """Ensure all Care DB tables exist and all columns are present.

    Called once at app startup after rxconfig.py has already connected the DB.
    In the production lab environment this is handled by SystemService.init_all_db().
    In the Reflex dev context, init_gws_env_and_db uses full_init=False which
    connects the DB but skips table creation and migrations — so we do both here.

    We apply each column addition directly via SqlMigrator.add_column_if_not_exists
    so it is idempotent and does not depend on the migration version tracking state.
    """
    try:
        from gws_care.core.care_db_manager import CareDbManager
        from gws_core.core.model.base_model_service import BaseModelService

        db_manager = CareDbManager.get_instance()
        if not db_manager.is_initialized():
            return

        # Ensure all model modules are imported so CareDbManager has the full model list
        import gws_care.core.care_app_config  # noqa: F401
        import gws_care.notification.notification_models  # noqa: F401
        import gws_care.patient.patient_account  # noqa: F401
        import gws_care.prescription.prescription  # noqa: F401
        import gws_care.role.user_care_role_account  # noqa: F401
        import gws_care.user.user_language_pref  # noqa: F401

        # 1. CREATE TABLE IF NOT EXISTS for all models
        # Wrapped in try/except: some DBs may raise (1118) Row size too large for
        # a new table schema. This must NOT abort the incremental migrations below.
        try:
            BaseModelService.create_database_tables(db_manager)
        except Exception as create_exc:
            print(f"[gws_care] Warning: create_database_tables failed (non-fatal): {create_exc}")

        # 2. Apply incremental column additions idempotently
        from gws_care.appointment.appointment import Appointment
        from gws_care.exam.exam import Exam
        from gws_care.exam.exam_file import ExamFile
        from gws_care.patient.patient import Patient
        from gws_core.core.db.migration.sql_migrator import SqlMigrator
        from peewee import CharField

        migrator = SqlMigrator(db_manager.db)
        # Migration 0.5.0 — document_type on exam_file
        migrator.add_column_if_not_exists(ExamFile, CharField(null=True), "document_type")
        migrator.migrate()

        # Migration 0.6.0 — billing_account_id FK on patient (raw SQL)
        if not Patient.column_exists("billing_account_id"):
            db_manager.db.execute_sql(
                "ALTER TABLE gws_care_patient ADD COLUMN billing_account_id VARCHAR(36) NULL DEFAULT NULL"
            )

        # Migration 0.7.0 — billing_account_id FK on appointment (raw SQL, copy from company_id)
        if not Appointment.column_exists("billing_account_id"):
            db_manager.db.execute_sql(
                "ALTER TABLE gws_care_appointment ADD COLUMN billing_account_id VARCHAR(36) NULL DEFAULT NULL"
            )
            db_manager.db.execute_sql(
                "UPDATE gws_care_appointment SET billing_account_id = company_id WHERE company_id IS NOT NULL"
            )

        # Migration 0.7.0 — billing_account_id FK on exam (raw SQL, copy from company_id)
        if not Exam.column_exists("billing_account_id"):
            db_manager.db.execute_sql(
                "ALTER TABLE gws_care_exam ADD COLUMN billing_account_id VARCHAR(36) NULL DEFAULT NULL"
            )
            db_manager.db.execute_sql(
                "UPDATE gws_care_exam SET billing_account_id = company_id WHERE company_id IS NOT NULL"
            )

        # Migration 0.8.0 — medical sections on exam
        for col, sql_type in [
            ("reason_for_visit", "TEXT"),
            ("medical_history", "TEXT"),
            ("weight", "DOUBLE"),
            ("height", "DOUBLE"),
            ("bmi", "DOUBLE"),
            ("blood_pressure", "VARCHAR(50)"),
            ("heart_rate", "DOUBLE"),
            ("temperature", "DOUBLE"),
            ("conclusion", "TEXT"),
        ]:
            if not Exam.column_exists(col):
                db_manager.db.execute_sql(
                    f"ALTER TABLE gws_care_exam ADD COLUMN {col} {sql_type} NULL DEFAULT NULL"
                )

        # Migration 0.9.0 — lab_results JSON on exam
        if not Exam.column_exists("lab_results"):
            db_manager.db.execute_sql(
                "ALTER TABLE gws_care_exam ADD COLUMN lab_results LONGTEXT NULL DEFAULT NULL"
            )

        # Migration 1.0.0 — smtp credentials_name replaces password on smtp_config
        from gws_care.notification.notification_models import SmtpConfig
        if SmtpConfig.column_exists("password") and not SmtpConfig.column_exists("credentials_name"):
            db_manager.db.execute_sql(
                "ALTER TABLE gws_care_smtp_config ADD COLUMN credentials_name VARCHAR(255) NULL DEFAULT NULL"
            )
            db_manager.db.execute_sql(
                "ALTER TABLE gws_care_smtp_config DROP COLUMN password"
            )
        elif not SmtpConfig.column_exists("credentials_name"):
            db_manager.db.execute_sql(
                "ALTER TABLE gws_care_smtp_config ADD COLUMN credentials_name VARCHAR(255) NULL DEFAULT NULL"
            )

        # Migration 1.1.0 — account_type on account (COMPANY / INDIVIDUAL)
        from gws_care.account.account import Account
        if not Account.column_exists("account_type"):
            db_manager.db.execute_sql(
                "ALTER TABLE gws_care_account ADD COLUMN account_type VARCHAR(20) NOT NULL DEFAULT 'COMPANY'"
            )

        # Migration 1.2.0 — recipient_phone on notification_log
        from gws_care.notification.notification_models import NotificationLog as NLog
        if not NLog.column_exists("recipient_phone"):
            db_manager.db.execute_sql(
                "ALTER TABLE gws_care_notification_log ADD COLUMN recipient_phone VARCHAR(50) NULL DEFAULT NULL"
            )

        # Migration 1.3.0 — linked_account_id / linked_patient_id on user_role
        from gws_care.role.user_care_role import UserCareRole
        if not UserCareRole.column_exists("linked_account_id"):
            db_manager.db.execute_sql(
                "ALTER TABLE gws_care_user_role ADD COLUMN linked_account_id VARCHAR(36) NULL DEFAULT NULL"
            )
        if not UserCareRole.column_exists("linked_patient_id"):
            db_manager.db.execute_sql(
                "ALTER TABLE gws_care_user_role ADD COLUMN linked_patient_id VARCHAR(36) NULL DEFAULT NULL"
            )

        # Migration 1.4.0 — Phase 4: QR codes
        # qr_code on patient
        if not Patient.column_exists("qr_code"):
            db_manager.db.execute_sql(
                "ALTER TABLE gws_care_patient ADD COLUMN qr_code LONGTEXT NULL DEFAULT NULL"
            )
        # tube_qr_code + is_done_on_site on exam
        if not Exam.column_exists("tube_qr_code"):
            db_manager.db.execute_sql(
                "ALTER TABLE gws_care_exam ADD COLUMN tube_qr_code VARCHAR(100) NULL DEFAULT NULL"
            )
        if not Exam.column_exists("is_done_on_site"):
            db_manager.db.execute_sql(
                "ALTER TABLE gws_care_exam ADD COLUMN is_done_on_site TINYINT(1) NOT NULL DEFAULT 0"
            )

        # Migration 1.5.0 — program_id, billing_account_id and interpretation fields on visit
        from gws_care.visit.visit import Visit
        if not Visit.column_exists("program_id"):
            db_manager.db.execute_sql(
                "ALTER TABLE gws_care_visit ADD COLUMN program_id VARCHAR(36) NULL DEFAULT NULL"
            )
        if not Visit.column_exists("billing_account_id"):
            db_manager.db.execute_sql(
                "ALTER TABLE gws_care_visit ADD COLUMN billing_account_id VARCHAR(36) NULL DEFAULT NULL"
            )
        if not Visit.column_exists("doctor_clinic_interpretation"):
            db_manager.db.execute_sql(
                "ALTER TABLE gws_care_visit ADD COLUMN doctor_clinic_interpretation LONGTEXT NULL DEFAULT NULL"
            )
        if not Visit.column_exists("doctor_company_interpretation"):
            db_manager.db.execute_sql(
                "ALTER TABLE gws_care_visit ADD COLUMN doctor_company_interpretation LONGTEXT NULL DEFAULT NULL"
            )
        if not Visit.column_exists("doctor_company_message"):
            db_manager.db.execute_sql(
                "ALTER TABLE gws_care_visit ADD COLUMN doctor_company_message LONGTEXT NULL DEFAULT NULL"
            )

        # Migration 1.6.0 — make account_id nullable on medical_program (individual programs)
        from gws_care.campaign.campaign import Campaign
        try:
            db_manager.db.execute_sql(
                "ALTER TABLE gws_care_medical_program MODIFY COLUMN account_id VARCHAR(36) NULL DEFAULT NULL"
            )
        except Exception:
            pass  # already nullable or column doesn't exist yet

        # Migration 1.7.0 — add is_individual flag to medical_program
        try:
            if not Campaign.column_exists("is_individual"):
                db_manager.db.execute_sql(
                    "ALTER TABLE gws_care_medical_program ADD COLUMN is_individual TINYINT(1) NOT NULL DEFAULT 0"
                )
        except Exception:
            pass

        # Migration 2.0.0 — patient_account join table (patient can belong to multiple accounts)
        try:
            cursor = db_manager.db.execute_sql("SHOW TABLES LIKE 'gws_care_patient_account'")
            has_join_table = cursor.fetchone() is not None
            if not has_join_table:
                db_manager.db.execute_sql(
                    "CREATE TABLE IF NOT EXISTS gws_care_patient_account ("
                    "  id VARCHAR(36) NOT NULL PRIMARY KEY,"
                    "  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,"
                    "  last_modified_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,"
                    "  created_by_id VARCHAR(36) NOT NULL,"
                    "  last_modified_by_id VARCHAR(36) NOT NULL,"
                    "  patient_id VARCHAR(36) NOT NULL,"
                    "  account_id VARCHAR(36) NOT NULL,"
                    "  UNIQUE KEY uniq_patient_account (patient_id, account_id)"
                    ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"
                )
                # Migrate existing billing_account_id links to the new join table
                if Patient.column_exists("billing_account_id"):
                    first_user = db_manager.db.execute_sql(
                        "SELECT id FROM gws_user LIMIT 1"
                    ).fetchone()
                    user_id = first_user[0] if first_user else None
                    if user_id:
                        db_manager.db.execute_sql(
                            "INSERT IGNORE INTO gws_care_patient_account"
                            "  (id, created_at, last_modified_at,"
                            "   created_by_id, last_modified_by_id, patient_id, account_id)"
                            " SELECT UUID(), NOW(), NOW(), %s, %s, p.id, p.billing_account_id"
                            " FROM gws_care_patient p"
                            " WHERE p.billing_account_id IS NOT NULL"
                            "   AND p.billing_account_id != ''",
                            (user_id, user_id),
                        )
        except Exception as mig_exc:
            print(f"[gws_care] Warning: migration 2.0.0 failed: {mig_exc}")

        # ── migration 3.1.0 — unique index on gws_care_account.name ─────────
        try:
            from gws_care.account.account import Account
            idx_rows = db_manager.db.execute_sql(
                "SELECT COUNT(*) FROM information_schema.statistics "
                "WHERE table_schema=DATABASE() AND table_name='gws_care_account' "
                "AND index_name='uniq_account_name'"
            ).fetchone()
            if idx_rows[0] == 0:
                db_manager.db.execute_sql(
                    "ALTER TABLE gws_care_account ADD UNIQUE INDEX uniq_account_name (name)"
                )
        except Exception as mig_exc:
            print(f"[gws_care] Warning: migration 3.1.0 (account unique name) failed: {mig_exc}")

        # ── migration 3.0.0 — MedicalCertificate extended columns ──────────────
        try:
            from gws_care.certificate.medical_certificate import MedicalCertificate
            _cert_columns = [                ("certificate_type", "VARCHAR(30) NOT NULL DEFAULT 'APTITUDE'"),
                ("start_date", "DATE NULL DEFAULT NULL"),
                ("end_date", "DATE NULL DEFAULT NULL"),
                ("return_date", "DATE NULL DEFAULT NULL"),
                ("exposure_type", "VARCHAR(120) NULL DEFAULT NULL"),
                ("vaccine_name", "VARCHAR(120) NULL DEFAULT NULL"),
                ("vaccine_lot", "VARCHAR(80) NULL DEFAULT NULL"),
                ("next_booster", "DATE NULL DEFAULT NULL"),
                ("accident_date", "DATE NULL DEFAULT NULL"),
                ("body_part", "VARCHAR(120) NULL DEFAULT NULL"),
                ("visit_subtype", "VARCHAR(80) NULL DEFAULT NULL"),
            ]
            for _col_name, _col_def in _cert_columns:
                if not MedicalCertificate.column_exists(_col_name):
                    db_manager.db.execute_sql(
                        f"ALTER TABLE gws_care_medical_certificate ADD COLUMN {_col_name} {_col_def}"
                    )
        except Exception as mig_exc:
            print(f"[gws_care] Warning: migration 3.0.0 (certificates) failed: {mig_exc}")

        # ── migration 3.2.0 — is_archived on prescription and certificate ────
        try:
            from gws_care.prescription.prescription import Prescription as _Presc
            if not _Presc.column_exists("is_archived"):
                db_manager.db.execute_sql(
                    "ALTER TABLE gws_care_prescription ADD COLUMN is_archived TINYINT(1) NOT NULL DEFAULT 0"
                )
        except Exception as mig_exc:
            print(f"[gws_care] Warning: migration 3.2.0 (prescription.is_archived) failed: {mig_exc}")

        try:
            from gws_care.certificate.medical_certificate import MedicalCertificate as _Cert
            if not _Cert.column_exists("is_archived"):
                db_manager.db.execute_sql(
                    "ALTER TABLE gws_care_medical_certificate ADD COLUMN is_archived TINYINT(1) NOT NULL DEFAULT 0"
                )
        except Exception as mig_exc:
            print(f"[gws_care] Warning: migration 3.2.0 (certificate.is_archived) failed: {mig_exc}")

        # ── migration 3.3.0 — color_theme on care_app_config ────────────────
        try:
            from gws_care.core.care_app_config import CareAppConfig
            if not CareAppConfig.column_exists("color_theme"):
                db_manager.db.execute_sql(
                    "ALTER TABLE gws_care_app_config ADD COLUMN color_theme VARCHAR(20) NOT NULL DEFAULT 'green'"
                )
        except Exception as mig_exc:
            print(f"[gws_care] Warning: migration 3.3.0 (color_theme) failed: {mig_exc}")

        # ── migration 3.4.0 — recipient_user + parent_log on notification_log ─
        try:
            from gws_care.notification.notification_models import NotificationLog
            if not NotificationLog.column_exists("recipient_user_id"):
                db_manager.db.execute_sql(
                    "ALTER TABLE gws_care_notification_log"
                    " ADD COLUMN recipient_user_id VARCHAR(36) NULL DEFAULT NULL"
                    " REFERENCES gws_care_user(id) ON DELETE SET NULL"
                )
        except Exception as mig_exc:
            print(f"[gws_care] Warning: migration 3.4.0 (recipient_user_id) failed: {mig_exc}")

        try:
            from gws_care.notification.notification_models import NotificationLog
            if not NotificationLog.column_exists("parent_log_id"):
                db_manager.db.execute_sql(
                    "ALTER TABLE gws_care_notification_log"
                    " ADD COLUMN parent_log_id VARCHAR(36) NULL DEFAULT NULL"
                    " REFERENCES gws_care_notification_log(id) ON DELETE SET NULL"
                )
        except Exception as mig_exc:
            print(f"[gws_care] Warning: migration 3.4.0 (parent_log_id) failed: {mig_exc}")

        # ── migration 3.5.0 — multi-role patient/account scoping ──────────────
        # Drop old single linked_account_id column from user_role table and
        # add all_patients flag + new gws_care_user_role_account join table.
        try:
            from gws_care.role.user_care_role import UserCareRole
            if UserCareRole.column_exists("linked_account_id"):
                db_manager.db.execute_sql(
                    "ALTER TABLE gws_care_user_role DROP COLUMN linked_account_id"
                )
        except Exception as mig_exc:
            print(f"[gws_care] Warning: migration 3.5.0 (drop linked_account_id) failed: {mig_exc}")

        try:
            from gws_care.role.user_care_role import UserCareRole
            if UserCareRole.column_exists("all_accounts"):
                # Rename legacy column if it was already added under the old name
                db_manager.db.execute_sql(
                    "ALTER TABLE gws_care_user_role RENAME COLUMN all_accounts TO all_patients"
                )
            elif not UserCareRole.column_exists("all_patients"):
                db_manager.db.execute_sql(
                    "ALTER TABLE gws_care_user_role"
                    " ADD COLUMN all_patients BOOLEAN NOT NULL DEFAULT 1"
                )
        except Exception as mig_exc:
            print(f"[gws_care] Warning: migration 3.5.0 (all_patients) failed: {mig_exc}")

        try:
            from gws_care.role.user_care_role_account import UserCareRoleAccount
            db_manager.db.create_tables([UserCareRoleAccount], safe=True)
        except Exception as mig_exc:
            print(f"[gws_care] Warning: migration 3.5.0 (user_role_account table) failed: {mig_exc}")

        # ── migration 3.6.0 — three visit types + classical/exam visit support ──
        # 1. visit_type column on gws_care_visit (default CAMPAIGN for existing rows)
        try:
            from gws_care.visit.visit import Visit as _Visit
            if not _Visit.column_exists("visit_type"):
                db_manager.db.execute_sql(
                    "ALTER TABLE gws_care_visit"
                    " ADD COLUMN visit_type VARCHAR(20) NOT NULL DEFAULT 'campaign'"
                )
        except Exception as mig_exc:
            print(f"[gws_care] Warning: migration 3.6.0 (visit_type) failed: {mig_exc}")

        # 2. closed_by_id + closed_at on gws_care_visit
        try:
            from gws_care.visit.visit import Visit as _Visit
            if not _Visit.column_exists("closed_by_id"):
                db_manager.db.execute_sql(
                    "ALTER TABLE gws_care_visit"
                    " ADD COLUMN closed_by_id VARCHAR(36) NULL DEFAULT NULL"
                )
            if not _Visit.column_exists("closed_at"):
                db_manager.db.execute_sql(
                    "ALTER TABLE gws_care_visit"
                    " ADD COLUMN closed_at DATETIME NULL DEFAULT NULL"
                )
        except Exception as mig_exc:
            print(f"[gws_care] Warning: migration 3.6.0 (closed_by/closed_at) failed: {mig_exc}")

        # 3. visit_id FK on gws_care_exam (column already exists as VARCHAR from phase 8 stub)
        #    No schema change needed — Peewee now treats it as a proper FK.

        # 4. visit_id FK on gws_care_prescription
        try:
            from gws_care.prescription.prescription import Prescription as _Presc
            if not _Presc.column_exists("visit_id"):
                db_manager.db.execute_sql(
                    "ALTER TABLE gws_care_prescription"
                    " ADD COLUMN visit_id VARCHAR(36) NULL DEFAULT NULL"
                )
        except Exception as mig_exc:
            print(f"[gws_care] Warning: migration 3.6.0 (prescription.visit_id) failed: {mig_exc}")

        # 5. visit_id FK on gws_care_medical_certificate
        try:
            from gws_care.certificate.medical_certificate import MedicalCertificate as _Cert
            if not _Cert.column_exists("visit_id"):
                db_manager.db.execute_sql(
                    "ALTER TABLE gws_care_medical_certificate"
                    " ADD COLUMN visit_id VARCHAR(36) NULL DEFAULT NULL"
                )
        except Exception as mig_exc:
            print(f"[gws_care] Warning: migration 3.6.0 (certificate.visit_id) failed: {mig_exc}")

        # ── migration 3.7.0 — rename classical/exam visit_type to consultation ──
        try:
            from gws_care.visit.visit import Visit as _Visit
            db_manager.db.execute_sql(
                "UPDATE gws_care_visit SET visit_type = 'consultation'"
                " WHERE visit_type IN ('classical', 'exam')"
            )
        except Exception as mig_exc:
            print(f"[gws_care] Warning: migration 3.7.0 (visit_type rename) failed: {mig_exc}")

        # ── migration 3.8.0 — rename visit.status → campaign_visit_status + add consultation_visit_status ──
        try:
            from gws_care.visit.visit import Visit as _Visit
            # Rename old 'status' column to 'campaign_visit_status' if it still exists
            if _Visit.column_exists("status") and not _Visit.column_exists("campaign_visit_status"):
                db_manager.db.execute_sql(
                    "ALTER TABLE gws_care_visit"
                    " CHANGE COLUMN status campaign_visit_status VARCHAR(255) NOT NULL DEFAULT 'pending'"
                )
            elif not _Visit.column_exists("campaign_visit_status"):
                db_manager.db.execute_sql(
                    "ALTER TABLE gws_care_visit"
                    " ADD COLUMN campaign_visit_status VARCHAR(255) NOT NULL DEFAULT 'pending'"
                )
            # Add consultation_visit_status if missing
            if not _Visit.column_exists("consultation_visit_status"):
                db_manager.db.execute_sql(
                    "ALTER TABLE gws_care_visit"
                    " ADD COLUMN consultation_visit_status VARCHAR(255) NULL DEFAULT NULL"
                )
        except Exception as mig_exc:
            print(f"[gws_care] Warning: migration 3.8.0 (campaign_visit_status rename) failed: {mig_exc}")

        # Seed ExamTypeModel from enum (idempotent — skips existing codes)
        # seed_from_enum() uses ModelWithUser which requires an auth context;
        # find the first admin user to provide one.
        try:
            from gws_care.exam.exam_type_service import ExamTypeService
            from gws_care.user.user import User as CareUser
            from gws_core import CurrentUserService
            from gws_core import User as GwsCoreUser
            seed_user = GwsCoreUser.select().first()
            if seed_user is not None:
                CurrentUserService.set_auth_user(seed_user)
                try:
                    ExamTypeService.seed_from_enum()
                finally:
                    CurrentUserService.clear_auth_context()
        except Exception as seed_exc:
            print(f"[gws_care] Warning: exam type seed skipped: {seed_exc}")

    except Exception as exc:
        # Non-fatal: the app will log the error when a query fails
        print(f"[gws_care] Warning: could not ensure DB tables/migrations: {exc}")


_ensure_care_db_tables()

app = register_gws_reflex_app()


@rx.page(route="/", on_load=[PatientListState.on_load, LanguageState.on_load, GeneralSettingsState.load_color_theme])
def index():
    """Main page — patient list."""
    return patient_list_page()


@rx.page(route="/patient/[patient_id_param]", on_load=[PatientDetailState.on_load, GeneralSettingsState.load_color_theme])
def patient_detail():
    """Patient detail page with exam history."""
    return patient_detail_page()


@rx.page(route="/accounts", on_load=[AccountListState.on_load, GeneralSettingsState.load_color_theme])
def account_list():
    """Client account management page."""
    return account_list_page()


@rx.page(route="/account/[account_id_param]", on_load=[AccountDetailState.on_load, GeneralSettingsState.load_color_theme])
def account_detail():
    """Account detail page with patient list."""
    return account_detail_page()


@rx.page(route="/exam/[exam_id_param]", on_load=[ExamDetailState.on_load, GeneralSettingsState.load_color_theme])
def exam_detail():
    """Exam detail page — results and doctor interpretation."""
    return exam_detail_page()


@rx.page(route="/visits", on_load=[VisitListState.on_load, LanguageState.on_load, GeneralSettingsState.load_color_theme])
def visits():
    """Scheduled visits page — list and calendar view, all types."""
    return visit_list_page()


@rx.page(route="/consultations", on_load=[VisitListState.on_load_consultations, LanguageState.on_load, GeneralSettingsState.load_color_theme])
def consultations():
    """Consultations page — visit list pre-filtered to consultation type."""
    return visit_list_page()


@rx.page(route="/campaign-visits", on_load=[VisitListState.on_load_campaign_visits, LanguageState.on_load, GeneralSettingsState.load_color_theme])
def campaign_visits():
    """Campaign visits page — visit list pre-filtered to campaign type."""
    return visit_list_page()


@rx.page(route="/settings", on_load=[AdminState.on_load, GeneralSettingsState.load_color_theme])
def settings():
    """Settings page — import, user roles, and notification configuration."""
    return settings_page()


@rx.page(route="/dashboard", on_load=[DashboardState.on_load, GeneralSettingsState.load_color_theme])
def dashboard():
    """Statistics dashboard."""
    return dashboard_page()


@rx.page(route="/notifications", on_load=[NotificationsState.on_load, GeneralSettingsState.load_color_theme])
def notifications():
    """Notifications — history, preferences and compose."""
    return notifications_page()


@rx.page(route="/campaigns", on_load=[CampaignListState.on_load, LanguageState.on_load, GeneralSettingsState.load_color_theme])
def campaigns():
    """Campaign list page."""
    return campaign_list_page()


@rx.page(route="/campaign/[campaign_id_param]", on_load=[CampaignDetailState.on_load, LanguageState.on_load, GeneralSettingsState.load_color_theme])
def campaign_detail():
    """Campaign detail page with patients, exam types and visits."""
    return campaign_detail_page()


@rx.page(route="/visit/[visit_id_param]", on_load=[VisitDetailState.on_load, LanguageState.on_load, GeneralSettingsState.load_color_theme])
def visit_detail():
    """Campaign visit detail page with exam results and interpretation workflow."""
    return visit_detail_page()


@rx.page(route="/consultation/[visit_id_param]", on_load=[ConsultationDetailState.on_load, LanguageState.on_load, GeneralSettingsState.load_color_theme])
def consultation_detail():
    """Medical consultation detail page."""
    return consultation_detail_page()


@rx.page(route="/my-results", on_load=[PatientPortalState.on_load_results, LanguageState.on_load, GeneralSettingsState.load_color_theme])
def my_results():
    """Patient portal — my completed results."""
    return my_results_page()


@rx.page(route="/my-appointments", on_load=[PatientPortalState.on_load_appointments, LanguageState.on_load, GeneralSettingsState.load_color_theme])
def my_appointments():
    """Patient portal — my appointments."""
    return my_appointments_page()


@rx.page(route="/my-messages", on_load=[PatientPortalState.on_load_messages, LanguageState.on_load, GeneralSettingsState.load_color_theme])
def my_messages():
    """Patient portal — my messages / notifications."""
    return my_messages_page()


@rx.page(route="/my-documents", on_load=[PatientPortalState.on_load_documents, LanguageState.on_load, GeneralSettingsState.load_color_theme])
def my_documents():
    """Patient portal — my medical certificates."""
    return my_documents_page()


@rx.page(route="/on-site/[program_id_param]", on_load=[TerrainState.on_load, LanguageState.on_load, GeneralSettingsState.load_color_theme])
def terrain():
    """Terrain page — mobile-optimised for Opérateur Terrain."""
    return terrain_page()


@rx.page(route="/prescription/[prescription_id_param]", on_load=[PrescriptionDetailState.on_load, GeneralSettingsState.load_color_theme])
def prescription_detail():
    """Prescription detail page."""
    return prescription_detail_page()


@rx.page(route="/certificate/[certificate_id_param]", on_load=[CertificateDetailState.on_load, GeneralSettingsState.load_color_theme])
def certificate_detail():
    """Certificate detail page."""
    return certificate_detail_page()


@rx.page(route="/switch_role", on_load=[SwitchRoleState.on_load, LanguageState.on_load, GeneralSettingsState.load_color_theme])
def switch_role():
    """Role selection page — choose which role to view the app as."""
    return switch_role_page()

