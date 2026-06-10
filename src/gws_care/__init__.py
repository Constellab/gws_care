# Models — must be imported so the ORM registers them (order: dependencies first)
from gws_care.account.account import Account
from gws_care.campaign.campaign import Campaign
from gws_care.campaign.campaign_exam_type import CampaignExamType
from gws_care.campaign.campaign_patient import CampaignPatient

# Reflex app task
from gws_care.care_app.generate_care_app import GenerateCareApp
from gws_care.certificate.medical_certificate import MedicalCertificate

# Migrations
from gws_care.core.migration_0 import Migration0190
from gws_care.core.migration_1 import Migration0200
from gws_care.core.migration_2 import Migration0210
from gws_care.core.migration_3 import Migration0220
from gws_care.core.migration_4 import Migration0230
from gws_care.core.migration_5 import Migration0240
from gws_care.core.migration_6 import Migration0250
from gws_care.core.migration_7 import Migration0260
from gws_care.core.migration_8 import Migration0270
from gws_care.core.migration_9 import Migration0280
from gws_care.core.migration_10 import Migration0290
from gws_care.document_upload.document_bulk_import_task import DocumentBulkImportTask
from gws_care.document_upload.document_text import DocumentText
from gws_care.document_upload.document_text_extraction_task import DocumentTextExtractionTask
from gws_care.document_upload.uploaded_document import UploadedDocument
from gws_care.exam.exam import Exam
from gws_care.exam.exam_result import ExamResult
from gws_care.exam.exam_type_model import ExamTypeModel
from gws_care.notification.notification_scheduler_task import CareNotificationSchedulerTask
from gws_care.patient.patient import Patient
from gws_care.patient.patient_doctor import PatientDoctor
from gws_care.role.user_care_role import UserCareRole

# User sync service — keeps local User table in sync with gws_core
from gws_care.user.care_user_sync_service import CareUserSyncService
from gws_care.user.user import User
from gws_care.user.user_app_config import UserAppConfig
from gws_care.visit.visit import Visit
from gws_care.workflow.campaign_validation_workflow import CampaignValidationWorkflow
from gws_care.workflow.campaign_visit_validation_workflow import CampaignVisitValidationWorkflow
from gws_care.workflow.exam_validation_workflow import ExamValidationWorkflow
