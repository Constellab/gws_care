# Models — must be imported so the ORM registers them (order: dependencies first)
from gws_care.account.account import Account
from gws_care.appointment.appointment import Appointment

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
from gws_care.exam.exam import Exam
from gws_care.exam.exam_result import ExamResult
from gws_care.patient.patient import Patient
from gws_care.role.user_care_role import UserCareRole

# User sync service — keeps local User table in sync with gws_core
from gws_care.user.care_user_sync_service import CareUserSyncService
from gws_care.user.user import User
