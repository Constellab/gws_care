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
from .doctor_list.doctor_list_component import doctor_list_page
from .doctor_list.doctor_list_state import DoctorListState


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


@rx.page(route="/doctors", on_load=[DoctorListState.on_load, LanguageState.on_load, GeneralSettingsState.load_color_theme])
def doctors():
    """Medical doctors registry page."""
    return doctor_list_page()


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

