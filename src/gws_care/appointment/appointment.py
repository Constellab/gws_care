"""Appointment model."""

from datetime import datetime

from gws_core import EnumField
from peewee import DateTimeField, ForeignKeyField, TextField

from gws_care.account.account import Account
from gws_care.appointment.appointment_status import AppointmentStatus
from gws_care.core.care_db_manager import CareDbManager
from gws_care.core.model_with_user import ModelWithUser
from gws_care.exam.exam_type import ExamType
from gws_care.patient.patient import Patient


class Appointment(ModelWithUser):
    """A scheduled health-check appointment for a patient.

    Lifecycle: SCHEDULED → IN_PROGRESS → DONE (or CANCELLED at any point).
    """

    patient: Patient = ForeignKeyField(
        Patient, null=False, backref="appointments", on_delete="CASCADE"
    )
    billing_account: Account = ForeignKeyField(
        Account, null=True, backref="appointments", on_delete="SET NULL"
    )
    scheduled_at: datetime = DateTimeField(null=False, index=True)
    exam_type: ExamType = EnumField(choices=ExamType, null=False)
    status: AppointmentStatus = EnumField(
        choices=AppointmentStatus, default=AppointmentStatus.SCHEDULED, null=False
    )
    notes: str = TextField(null=True)

    class Meta:
        table_name = "gws_care_appointment"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
