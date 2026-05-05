import reflex as rx
from gws_reflex_main import ReflexMainState, main_component, register_gws_reflex_app

from .account_detail.account_detail_component import account_detail_page
from .account_detail.account_detail_state import AccountDetailState
from .account_list.account_list_component import account_list_page
from .account_list.account_list_state import AccountListState
from .admin.admin_component import settings_page
from .admin.admin_state import AdminState
from .appointment_list.appointment_list_component import appointment_list_page
from .appointment_list.appointment_list_state import AppointmentListState
from .common.language_state import LanguageState
from .common.page_layout import page_layout
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

    except Exception as exc:
        # Non-fatal: the app will log the error when a query fails
        print(f"[gws_care] Warning: could not ensure DB tables/migrations: {exc}")


_ensure_care_db_tables()

app = register_gws_reflex_app()


@rx.page(route="/", on_load=[PatientListState.on_load, LanguageState.on_load])
def index():
    """Main page — patient list."""
    return patient_list_page()


@rx.page(route="/patient/[patient_id_param]", on_load=[PatientDetailState.on_load])
def patient_detail():
    """Patient detail page with exam history."""
    return patient_detail_page()


@rx.page(route="/accounts", on_load=[AccountListState.on_load])
def account_list():
    """Client account management page."""
    return account_list_page()


@rx.page(route="/account/[account_id_param]", on_load=[AccountDetailState.on_load])
def account_detail():
    """Account detail page with patient list."""
    return account_detail_page()


@rx.page(route="/exam/[exam_id_param]", on_load=[ExamDetailState.on_load])
def exam_detail():
    """Exam detail page — results and doctor interpretation."""
    return exam_detail_page()


@rx.page(route="/appointments", on_load=[AppointmentListState.on_load])
def appointments():
    """Appointment scheduling page."""
    return appointment_list_page()


@rx.page(route="/settings", on_load=[AdminState.on_load, NotificationsState.on_load, LanguageState.on_load])
def settings():
    """Settings page — import, user roles, and notification configuration."""
    return settings_page()


@rx.page(route="/dashboard", on_load=[DashboardState.on_load])
def dashboard():
    """Statistics dashboard."""
    return dashboard_page()


@rx.page(route="/notifications", on_load=[NotificationsState.on_load])
def notifications():
    """Notifications — history, preferences and compose."""
    return notifications_page()

