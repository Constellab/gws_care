# Models — must be imported so the ORM registers them (order: dependencies first)
from gws_care.account.account import Account
from gws_care.appointment.appointment import Appointment
from gws_care.audit.audit_log import AuditLog
from gws_care.billing.patient_invoice import PatientInvoice, PatientInvoiceLine
from gws_care.billing.price_list import PriceList
from gws_care.campaign.campaign import Campaign
from gws_care.campaign.campaign_exam import CampaignExam
from gws_care.campaign.campaign_patient import CampaignPatient
from gws_care.certificate.medical_certificate import MedicalCertificate
from gws_care.company.company import Company
from gws_care.consultation.consultation import Consultation
from gws_care.correction.correction_request import CorrectionRequest
from gws_care.dashboard.dashboard_snapshot import DashboardSnapshot
from gws_care.exam.exam import Exam
from gws_care.exam.exam_file import ExamFile
from gws_care.exam.exam_parameter_result import ExamParameterResult
from gws_care.exam.exam_result import ExamResult
from gws_care.exam_type_ref.exam_parameter import ExamParameter
from gws_care.exam_type_ref.exam_type_ref import ExamTypeRef
from gws_care.messaging.patient_message import PatientMessage
from gws_care.notification.notification_models import (
    BrevoConfig,
    NotificationBell,
    NotificationLog,
    NotificationPreference,
    SmtpConfig,
)
from gws_care.patient.patient import Patient
from gws_care.patient.patient_consent import PatientConsent
from gws_care.patient.patient_deletion_log import PatientDeletionLog
from gws_care.patient.patient_document import PatientDocument
from gws_care.patient.patient_note import PatientNote
from gws_care.patient_account.patient_account import PatientAccount
from gws_care.prebilling.prebilling import Invoice, Prebilling, PrebillingLine
from gws_care.prescription.prescription import Prescription, PrescriptionLine
from gws_care.role.user_care_role import UserCareRole
from gws_care.scheduling.doctor_schedule import DoctorSchedule, DoctorUnavailableDay
from gws_care.tube_qr.tube_qr import TubeQR
from gws_care.user.user_language_pref import UserLanguagePref

# Reflex app task
from gws_care.care_app.generate_care_app import GenerateCareApp

# Migrations (in version order)
from gws_care.core.migration_0 import Migration010
from gws_care.core.migration_1 import Migration020
from gws_care.core.migration_2 import Migration030
from gws_care.core.migration_3 import Migration040
from gws_care.core.migration_4 import Migration050
from gws_care.core.migration_5 import Migration060
from gws_care.core.migration_6 import Migration070
from gws_care.core.migration_7 import Migration080
from gws_care.core.migration_8 import Migration090
from gws_care.core.migration_9 import Migration091
from gws_care.core.migration_10 import Migration100
from gws_care.core.migration_11 import Migration101
from gws_care.core.migration_12 import Migration102
from gws_care.core.migration_13 import Migration103
from gws_care.core.migration_14 import Migration104
from gws_care.core.migration_15 import Migration105
from gws_care.core.migration_16 import Migration106
from gws_care.core.migration_17 import Migration107
from gws_care.core.migration_18 import Migration108
from gws_care.core.migration_19 import Migration109

# User sync service — keeps local User table in sync with gws_core
from gws_care.user.care_user_sync_service import CareUserSyncService
from gws_care.user.user import User
