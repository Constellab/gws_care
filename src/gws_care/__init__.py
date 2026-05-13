# Models — must be imported so the ORM registers them (order: dependencies first)
from gws_care.account.account import Account
from gws_care.appointment.appointment import Appointment
from gws_care.medical_program.medical_program import MedicalProgram
from gws_care.medical_program.medical_program_exam_type import ProgramExamType
from gws_care.medical_program.medical_program_patient import ProgramPatient

# Reflex app task
from gws_care.care_app.generate_care_app import GenerateCareApp
from gws_care.certificate.medical_certificate import MedicalCertificate

# Migrations
from gws_care.core.migration_0 import Migration0170
from gws_care.exam.exam import Exam
from gws_care.exam.exam_result import ExamResult
from gws_care.exam.exam_type_model import ExamTypeModel
from gws_care.notification.notification_scheduler_task import CareNotificationSchedulerTask
from gws_care.patient.patient import Patient
from gws_care.role.user_care_role import UserCareRole

# User sync service — keeps local User table in sync with gws_core
from gws_care.user.care_user_sync_service import CareUserSyncService
from gws_care.user.user import User
from gws_care.visit.visit import Visit
from gws_care.workflow.program_validation_workflow import ProgramValidationWorkflow
from gws_care.workflow.visit_validation_workflow import VisitValidationWorkflow
