import reflex as rx
from gws_reflex_main import ReflexMainState, main_component, register_gws_reflex_app

from .account_detail.account_detail_component import account_detail_page
from .account_detail.account_detail_state import AccountDetailState
from .account_list.account_list_component import account_list_page
from .account_list.account_list_state import AccountListState
from .admin.admin_component import settings_page
from .admin.admin_state import AdminState
from .company_detail.company_detail_component import company_detail_page
from .company_detail.company_detail_state import CompanyDetailState
from .company_list.company_list_component import company_list_page
from .company_list.company_list_state import CompanyListState
from .appointment_list.appointment_list_component import appointment_list_page
from .appointment_list.appointment_list_state import AppointmentListState
from .audit_page.audit_component import audit_page
from .audit_page.audit_state import AuditState
from .campaign_detail.campaign_detail_component import campaign_detail_page
from .campaign_detail.campaign_detail_state import CampaignDetailState
from .campaign_detail.campaign_patient_exams_component import campaign_patient_exams_page
from .campaign_detail.campaign_patient_exams_state import CampaignPatientExamsState
from .campaign_list.campaign_list_component import campaigns_list_page
from .campaign_list.campaign_list_state import CampaignListState
from .common.language_state import LanguageState
from .common.nav_role_state import NavRoleState
from .common.page_layout import page_layout
from .dashboard.dashboard_component import dashboard_page
from .dashboard.dashboard_state import DashboardState
from .doctor_enterprise.doctor_enterprise_component import doctor_enterprise_page
from .doctor_enterprise.doctor_enterprise_state import DoctorEnterpriseState
from .doctor_psc.doctor_psc_component import doctor_psc_page
from .doctor_psc.doctor_psc_state import DoctorPscState
from .exam_detail.exam_detail_component import exam_detail_page
from .exam_detail.exam_detail_state import ExamDetailState
from .exam_types.exam_types_component import exam_types_page
from .exam_types.exam_types_state import ExamTypesState
from .hr_portal.hr_portal_component import hr_portal_page
from .hr_portal.hr_portal_state import HRPortalState
from .notifications.notifications_component import notifications_page
from .notifications.notifications_state import NotificationsState
from .patient_detail.patient_detail_component import patient_detail_page
from .patient_detail.patient_detail_state import PatientDetailState
from .patient_detail.patient_dossier_state import PatientDossierState
from .patient_list.patient_list_component import patient_list_page
from .patient_list.patient_list_state import PatientListState
from .prebilling_page.prebilling_component import prebilling_page
from .prebilling_page.prebilling_state import PrebillingState
from .user_management.user_management_component import user_management_page
from .user_management.user_management_state import UserManagementState


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
        import gws_care.notification.notification_models  # noqa: F401
        import gws_care.user.user_language_pref  # noqa: F401

        # 1. CREATE TABLE IF NOT EXISTS for all models
        BaseModelService.create_database_tables(db_manager)

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

        # Migration 1.2.0 — recipient_phone on notification_log; BrevoConfig table
        from gws_care.notification.notification_models import BrevoConfig
        from gws_care.notification.notification_models import NotificationLog as NLog
        if not NLog.column_exists("recipient_phone"):
            db_manager.db.execute_sql(
                "ALTER TABLE gws_care_notification_log ADD COLUMN recipient_phone VARCHAR(50) NULL DEFAULT NULL"
            )
        # BrevoConfig table is created by BaseModelService.create_database_tables above

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

        # Migration 0.10.0 — Campaign and CampaignPatient tables (V2 dashboard)
        import gws_care.campaign.campaign  # noqa: F401
        import gws_care.campaign.campaign_patient  # noqa: F401
        from gws_care.campaign.campaign import Campaign
        from gws_care.campaign.campaign_patient import CampaignPatient
        db_manager.db.create_tables([Campaign, CampaignPatient], safe=True)

        # Migration 0.10.0 — new V2 domain tables
        import gws_care.audit.audit_log  # noqa: F401
        import gws_care.campaign.campaign_exam  # noqa: F401
        import gws_care.correction.correction_request  # noqa: F401
        import gws_care.exam_type_ref.exam_parameter  # noqa: F401
        import gws_care.exam_type_ref.exam_type_ref  # noqa: F401
        import gws_care.patient_account.patient_account  # noqa: F401
        import gws_care.prebilling.prebilling  # noqa: F401
        import gws_care.tube_qr.tube_qr  # noqa: F401
        from gws_care.audit.audit_log import AuditLog
        from gws_care.campaign.campaign_exam import CampaignExam
        from gws_care.correction.correction_request import CorrectionRequest
        from gws_care.exam_type_ref.exam_parameter import ExamParameter
        from gws_care.exam_type_ref.exam_type_ref import ExamTypeRef
        from gws_care.patient_account.patient_account import PatientAccount
        from gws_care.prebilling.prebilling import Invoice, Prebilling, PrebillingLine
        from gws_care.tube_qr.tube_qr import TubeQR
        db_manager.db.create_tables(
            [PatientAccount, ExamTypeRef, ExamParameter, CampaignExam,
             TubeQR, Prebilling, PrebillingLine, Invoice, CorrectionRequest, AuditLog],
            safe=True,
        )
        # Add medical workflow columns to gws_care_campaign_patient (idempotent)
        for col_def in [
            ("medical_status", "VARCHAR(30) NOT NULL DEFAULT 'PENDING'"),
            ("psc_notes", "TEXT NULL DEFAULT NULL"),
            ("enterprise_notes", "TEXT NULL DEFAULT NULL"),
            ("patient_message", "TEXT NULL DEFAULT NULL"),
            ("psc_validated_at", "DATETIME NULL DEFAULT NULL"),
            ("enterprise_validated_at", "DATETIME NULL DEFAULT NULL"),
            ("published_at", "DATETIME NULL DEFAULT NULL"),
        ]:
            db_manager.db.execute_sql(
                f"ALTER TABLE gws_care_campaign_patient "
                f"ADD COLUMN IF NOT EXISTS {col_def[0]} {col_def[1]}"
            )

        # Migration 0.10.1 — gws_care_company table (employeurs) + company_id on patient
        from gws_care.company.company import Company
        db_manager.db.create_tables([Company], safe=True)
        if not Patient.column_exists("company_id"):
            db_manager.db.execute_sql(
                "ALTER TABLE gws_care_patient ADD COLUMN company_id VARCHAR(36) NULL DEFAULT NULL"
            )

        # Migration 0.10.2 — patient documents and doctor notes (dossier-level)
        import gws_care.patient.patient_document  # noqa: F401
        import gws_care.patient.patient_note  # noqa: F401
        from gws_care.patient.patient_document import PatientDocument
        from gws_care.patient.patient_note import PatientNote
        db_manager.db.create_tables([PatientDocument, PatientNote], safe=True)

    except Exception as exc:
        # Non-fatal: the app will log the error when a query fails
        print(f"[gws_care] Warning: could not ensure DB tables/migrations: {exc}")


_ensure_care_db_tables()

app = register_gws_reflex_app()


@rx.page(route="/", on_load=[PatientListState.on_load, LanguageState.on_load, NavRoleState.on_load])
def index():
    """Main page — patient list."""
    return patient_list_page()


@rx.page(route="/patient/[patient_id_param]", on_load=[PatientDetailState.on_load, PatientDossierState.load_dossier, NavRoleState.on_load])
def patient_detail():
    """Patient detail page with exam history."""
    return patient_detail_page()


@rx.page(route="/accounts", on_load=[AccountListState.on_load, NavRoleState.on_load])
def account_list():
    """Client account management page."""
    return account_list_page()


@rx.page(route="/account/[account_id_param]", on_load=[AccountDetailState.on_load, NavRoleState.on_load])
def account_detail():
    """Account detail page with patient list."""
    return account_detail_page()


@rx.page(route="/exam/[exam_id_param]", on_load=[ExamDetailState.on_load, NavRoleState.on_load])
def exam_detail():
    """Exam detail page — results and doctor interpretation."""
    return exam_detail_page()


@rx.page(route="/appointments", on_load=[AppointmentListState.on_load, NavRoleState.on_load])
def appointments():
    """Appointment scheduling page."""
    return appointment_list_page()


@rx.page(route="/settings", on_load=[AdminState.on_load, NotificationsState.on_load, LanguageState.on_load, NavRoleState.on_load])
def settings():
    """Settings page — import, user roles, and notification configuration."""
    return settings_page()


@rx.page(route="/dashboard", on_load=[DashboardState.on_load, NavRoleState.on_load])
def dashboard():
    """Statistics dashboard."""
    return dashboard_page()


@rx.page(route="/campaigns", on_load=[CampaignListState.on_load, NavRoleState.on_load])
def campaigns():
    """Campaigns list page."""
    return campaigns_list_page()


@rx.page(route="/campaign/[campaign_id_param]", on_load=[CampaignDetailState.on_load, NavRoleState.on_load])
def campaign_detail():
    """Campaign detail page with full workflow."""
    return campaign_detail_page()


@rx.page(
    route="/campaign-patient/[cp_campaign_id]/[cp_patient_id]",
    on_load=[CampaignPatientExamsState.on_load, NavRoleState.on_load],
)
def campaign_patient_exams():
    """Per-patient exam results entry page within a campaign."""
    return campaign_patient_exams_page()


@rx.page(route="/users", on_load=[UserManagementState.on_load, NavRoleState.on_load])
def user_management():
    """User management page — PSC and enterprise users."""
    return user_management_page()


@rx.page(route="/exam-types", on_load=[ExamTypesState.on_load, NavRoleState.on_load])
def exam_types():
    """Exam type referential management."""
    return exam_types_page()


@rx.page(route="/doctor-psc", on_load=[DoctorPscState.on_load, NavRoleState.on_load])
def doctor_psc():
    """Médecin PSC interpretation queue."""
    return doctor_psc_page()


@rx.page(route="/doctor-enterprise", on_load=[DoctorEnterpriseState.on_load, NavRoleState.on_load])
def doctor_enterprise():
    """Médecin entreprise interpretation and publication."""
    return doctor_enterprise_page()


@rx.page(route="/hr", on_load=[HRPortalState.on_load, NavRoleState.on_load])
def hr_portal():
    """RH enterprise administrative portal."""
    return hr_portal_page()


@rx.page(route="/prebilling", on_load=[PrebillingState.on_load, NavRoleState.on_load])
def prebilling():
    """Pre-billing and invoice management."""
    return prebilling_page()


@rx.page(route="/audit", on_load=[AuditState.on_load, NavRoleState.on_load])
def audit():
    """Audit log — action traceability."""
    return audit_page()


@rx.page(route="/notifications", on_load=[NotificationsState.on_load, NavRoleState.on_load])
def notifications():
    """Notifications — history, preferences and compose."""
    return notifications_page()


@rx.page(route="/companies", on_load=[CompanyListState.on_load, NavRoleState.on_load])
def company_list():
    """Company list page."""
    return company_list_page()


@rx.page(route="/company/[company_id_param]", on_load=[CompanyDetailState.on_load, NavRoleState.on_load])
def company_detail():
    """Company detail page."""
    return company_detail_page()

