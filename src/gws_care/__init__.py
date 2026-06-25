# Models — must be imported so the ORM registers them (order: dependencies first)

# Core user and account models
from gws_care.user.user import User
from gws_care.user.user_language_pref import UserLanguagePref
from gws_care.user.user_app_config import UserAppConfig

from gws_care.account.account import Account
from gws_care.company.company import Company

# Patient models (patient_account depends on patient + account)
from gws_care.patient.patient import Patient
from gws_care.patient.patient_account import PatientAccount
from gws_care.patient.patient_doctor import PatientDoctor
from gws_care.patient.patient_consent import PatientConsent
from gws_care.patient.patient_deletion_log import PatientDeletionLog
from gws_care.patient.patient_document import PatientDocument
from gws_care.patient.patient_note import PatientNote

# Role models
from gws_care.role.user_care_role import UserCareRole

# Doctor model
from gws_care.doctor.medical_doctor import MedicalDoctor

# Campaign models
from gws_care.campaign.campaign import Campaign
from gws_care.campaign.campaign_doctor import CampaignDoctor
from gws_care.campaign.campaign_exam_type import CampaignExamType
from gws_care.campaign.campaign_patient import CampaignPatient

# Visit model (depends on campaign, patient, account, doctor)
from gws_care.visit.visit import Visit

# Exam models (depend on visit, patient, account)
from gws_care.exam.exam import Exam
from gws_care.exam.exam_result import ExamResult
from gws_care.exam.exam_type_model import ExamTypeModel

# Certificate
from gws_care.certificate.medical_certificate import MedicalCertificate

# Notifications
from gws_care.notification.notification_models import (
    BrevoConfig,
    NotificationBell,
    NotificationLog,
    NotificationPreference,
    SmtpConfig,
)

# Document upload (AI analysis)
from gws_care.document_upload.document_text import DocumentText
from gws_care.document_upload.uploaded_document import UploadedDocument

# Audit
from gws_care.audit.audit_log import AuditLog

# Dashboard
from gws_care.dashboard.dashboard_snapshot import DashboardSnapshot

# Billing / invoicing
from gws_care.billing.patient_invoice import PatientInvoice, PatientInvoiceLine
from gws_care.billing.price_list import PriceList

# Prescriptions
from gws_care.prescription.prescription import Prescription

# TubeQR
from gws_care.tube_qr.tube_qr import TubeQR

# Messaging
from gws_care.messaging.patient_message import PatientMessage

# Exam file / parameter results
from gws_care.exam.exam_file import ExamFile
from gws_care.exam.exam_parameter_result import ExamParameterResult

# Exam type referential (configurable exam types + parameters)
from gws_care.exam_type_ref.exam_type_ref import ExamTypeRef
from gws_care.exam_type_ref.exam_parameter import ExamParameter

# Scheduling
from gws_care.scheduling.doctor_schedule import DoctorSchedule, DoctorUnavailableDay

# Reflex app task
from gws_care.care_app.generate_care_app import GenerateCareApp

# Background tasks
from gws_care.notification.notification_scheduler_task import CareNotificationSchedulerTask
from gws_care.document_upload.document_bulk_import_task import DocumentBulkImportTask
from gws_care.document_upload.document_text_extraction_task import DocumentTextExtractionTask

# Workflow gating models
from gws_care.workflow.campaign_validation_workflow import CampaignValidationWorkflow
from gws_care.workflow.campaign_visit_validation_workflow import CampaignVisitValidationWorkflow
from gws_care.workflow.exam_validation_workflow import ExamValidationWorkflow

# Migrations (in version order — run on startup to bring DB to current schema)
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
from gws_care.core.migration_20 import Migration200
from gws_care.core.migration_21 import Migration210
from gws_care.core.migration_22 import Migration220
from gws_care.core.migration_23 import Migration230
from gws_care.core.migration_24 import Migration240
from gws_care.core.migration_25 import Migration250
from gws_care.core.migration_26 import Migration260
from gws_care.core.migration_27 import Migration270
from gws_care.core.migration_28 import Migration280
from gws_care.core.migration_29 import Migration290
from gws_care.core.migration_30 import Migration300
from gws_care.core.migration_31 import Migration310

# User sync service — keeps local User table in sync with gws_core
from gws_care.user.care_user_sync_service import CareUserSyncService
