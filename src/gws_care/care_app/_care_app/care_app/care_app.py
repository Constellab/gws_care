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
from .patient_portal.patient_appointments_component import patient_appointments_page
from .patient_portal.patient_appointments_state import PatientAppointmentsState
from .patient_portal.patient_dashboard_state import PatientDashboardState
from .patient_portal.patient_dashboard_component import patient_dashboard_page
from .patient_portal.patient_details_state import PatientDetailsState
from .patient_portal.patient_details_component import patient_details_page
from .patient_portal.patient_consultations_state import PatientConsultationsState
from .patient_portal.patient_consultations_component import patient_consultations_page
from .patient_portal.patient_notifications_state import PatientNotificationsState
from .patient_portal.patient_notifications_component import patient_notifications_page
from .patient_portal.patient_documents_state import PatientDocumentsState
from .patient_portal.patient_documents_component import (
    my_exams_page,
    my_prescriptions_page,
    my_certificates_page,
    my_all_documents_page,
)
from .patient_portal.patient_accounts_state import PatientAccountsState
from .patient_portal.patient_accounts_component import patient_accounts_page
from .prescription_detail.prescription_detail_component import prescription_detail_page
from .prescription_detail.prescription_detail_state import PrescriptionDetailState
from .no_access.no_access_component import no_access_page
from .no_access.not_found_component import not_found_page
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
from .admin_documents.admin_documents_component import admin_documents_page
from .admin_documents.admin_documents_state import AdminDocumentsState
from .appointments_list.appointments_list_component import appointments_list_page
from .appointments_list.appointments_list_state import AppointmentsListState
from .appointment_detail.appointment_detail_component import appointment_detail_page
from .appointment_detail.appointment_detail_state import AppointmentDetailState
from .document_upload.document_upload_component import document_upload_page
from .document_upload.document_upload_state import DocumentUploadState
from .uploaded_document_detail.uploaded_document_detail_component import uploaded_document_detail_page
from .uploaded_document_detail.uploaded_document_detail_state import UploadedDocumentDetailState


app = register_gws_reflex_app()
app.add_page(not_found_page, route="404")


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


@rx.page(route="/appointments", on_load=[AppointmentsListState.on_load, LanguageState.on_load, GeneralSettingsState.load_color_theme])
def appointments():
    """Appointments page — scheduling view of consultation visits."""
    return appointments_list_page()


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


@rx.page(route="/settings", on_load=[AdminState.on_load, NotificationsState.load_settings, GeneralSettingsState.on_load])
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


@rx.page(route="/appointment/[visit_id_param]", on_load=[AppointmentDetailState.on_load, LanguageState.on_load, GeneralSettingsState.load_color_theme])
def appointment_detail():
    """Appointment detail page — view, edit, cancel/delete a single appointment."""
    return appointment_detail_page()


@rx.page(route="/consultation/[visit_id_param]", on_load=[ConsultationDetailState.on_load, LanguageState.on_load, GeneralSettingsState.load_color_theme])
def consultation_detail():
    """Medical consultation detail page."""
    return consultation_detail_page()


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


@rx.page(route="/my-appointments", on_load=[PatientAppointmentsState.on_load, LanguageState.on_load, GeneralSettingsState.load_color_theme])
def my_appointments():
    """Patient portal — plan and view appointments."""
    return patient_appointments_page()


@rx.page(route="/patient-dashboard", on_load=[PatientDashboardState.on_load, LanguageState.on_load, GeneralSettingsState.load_color_theme])
def patient_dashboard():
    """Patient portal — personal dashboard with KPIs and recent activity."""
    return patient_dashboard_page()


@rx.page(route="/my-details", on_load=[PatientDetailsState.on_load, PatientAccountsState.on_load, LanguageState.on_load, GeneralSettingsState.load_color_theme])
def my_details():
    """Patient portal — my personal information and accounts."""
    return patient_details_page()


@rx.page(route="/my-consultations", on_load=[PatientConsultationsState.on_load, LanguageState.on_load, GeneralSettingsState.load_color_theme])
def my_consultations():
    """Patient portal — my consultations filtered to this patient."""
    return patient_consultations_page()


@rx.page(route="/my-notifications", on_load=[PatientNotificationsState.on_load, LanguageState.on_load, GeneralSettingsState.load_color_theme])
def my_notifications():
    """Patient portal — my notifications inbox."""
    return patient_notifications_page()


@rx.page(route="/my-exams", on_load=[PatientDocumentsState.on_load_exams, LanguageState.on_load, GeneralSettingsState.load_color_theme])
def my_exams():
    """Patient portal — my exams."""
    return my_exams_page()


@rx.page(route="/my-prescriptions", on_load=[PatientDocumentsState.on_load_prescriptions, LanguageState.on_load, GeneralSettingsState.load_color_theme])
def my_prescriptions():
    """Patient portal — my prescriptions."""
    return my_prescriptions_page()


@rx.page(route="/my-certificates", on_load=[PatientDocumentsState.on_load_certificates, LanguageState.on_load, GeneralSettingsState.load_color_theme])
def my_certificates():
    """Patient portal — my medical certificates."""
    return my_certificates_page()


@rx.page(route="/my-all-documents", on_load=[PatientDocumentsState.on_load_all_documents, LanguageState.on_load, GeneralSettingsState.load_color_theme])
def my_all_documents():
    """Patient portal — all my documents (exams, prescriptions, certificates)."""
    return my_all_documents_page()


@rx.page(route="/my-patient-accounts", on_load=[PatientAccountsState.on_load, LanguageState.on_load, GeneralSettingsState.load_color_theme])
def my_patient_accounts():
    """Patient portal — my associated accounts."""
    return patient_accounts_page()


@rx.page(route="/documents", on_load=[AdminDocumentsState.on_load, LanguageState.on_load, GeneralSettingsState.load_color_theme])
def documents():
    """Admin documents page — browse all patient documents across the platform."""
    return admin_documents_page()


@rx.page(route="/documents/upload", on_load=[DocumentUploadState.on_load, LanguageState.on_load, GeneralSettingsState.load_color_theme])
def documents_upload():
    """Document upload page — drop a file, AI analysis, manual annotation, save."""
    return document_upload_page()


@rx.page(route="/document/[doc_id]", on_load=[UploadedDocumentDetailState.on_load, LanguageState.on_load, GeneralSettingsState.load_color_theme])
def uploaded_document_detail():
    """Uploaded document detail page — view metadata and open the file."""
    return uploaded_document_detail_page()


@rx.page(route="/no-access", on_load=[LanguageState.on_load])
def no_access():
    """No access page — shown when the user has no CareRole assigned."""
    return no_access_page()


@rx.page(route="/switch_role", on_load=[SwitchRoleState.on_load, LanguageState.on_load, GeneralSettingsState.load_color_theme])
def switch_role():
    """Role selection page — choose which role to view the app as."""
    return switch_role_page()

