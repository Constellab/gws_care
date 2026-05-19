# Models — must be imported so the ORM registers them (order: dependencies first)
from gws_care.account.account import Account
from gws_care.appointment.appointment import Appointment
from gws_care.campaign.campaign import Campaign
from gws_care.campaign.campaign_exam_type import CampaignExamType
from gws_care.campaign.campaign_patient import CampaignPatient
from gws_care.campaign_visit.campaign_visit import CampaignVisit

# Reflex app task
from gws_care.care_app.generate_care_app import GenerateCareApp
from gws_care.certificate.medical_certificate import MedicalCertificate

# Migrations
from gws_care.core.migration_0 import Migration0170
from gws_care.core.migration_1 import Migration0180
from gws_care.exam.exam import Exam
from gws_care.exam.exam_result import ExamResult
from gws_care.exam.exam_type_model import ExamTypeModel
from gws_care.notification.notification_scheduler_task import CareNotificationSchedulerTask
from gws_care.patient.patient import Patient
from gws_care.role.user_care_role import UserCareRole

# User sync service — keeps local User table in sync with gws_core
from gws_care.user.care_user_sync_service import CareUserSyncService
from gws_care.user.user import User
from gws_care.workflow.program_validation_workflow import CampaignValidationWorkflow
from gws_care.workflow.visit_validation_workflow import CampaignVisitValidationWorkflow
