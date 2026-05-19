# Models — must be imported so the ORM registers them (order: dependencies first)
from gws_care.account.account import Account
from gws_care.appointment.appointment import Appointment
from gws_care.audit.audit_log import AuditLog
from gws_care.campaign.campaign import Campaign
from gws_care.campaign.campaign_exam import CampaignExam
from gws_care.campaign.campaign_patient import CampaignPatient
from gws_care.correction.correction_request import CorrectionRequest

# Reflex app task
from gws_care.care_app.generate_care_app import GenerateCareApp
from gws_care.certificate.medical_certificate import MedicalCertificate

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
from gws_care.exam.exam import Exam
from gws_care.exam.exam_result import ExamResult
from gws_care.exam_type_ref.exam_parameter import ExamParameter
from gws_care.exam_type_ref.exam_type_ref import ExamTypeRef
from gws_care.patient.patient import Patient
from gws_care.patient_account.patient_account import PatientAccount
from gws_care.prebilling.prebilling import Invoice, Prebilling, PrebillingLine
from gws_care.role.user_care_role import UserCareRole
from gws_care.tube_qr.tube_qr import TubeQR

# User sync service — keeps local User table in sync with gws_core
from gws_care.user.care_user_sync_service import CareUserSyncService
from gws_care.user.user import User
