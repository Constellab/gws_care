"""Appointment model."""

from datetime import datetime

from gws_core import EnumField
from peewee import CharField, DateTimeField, ForeignKeyField, IntegerField, TextField

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
    exam_type_ref_id: str = CharField(max_length=36, null=True, default=None)
    status: AppointmentStatus = EnumField(
        choices=AppointmentStatus, default=AppointmentStatus.SCHEDULED, null=False
    )
    notes: str = TextField(null=True)
    # Doctor assignment (set via planning view)
    assigned_doctor_id: str = CharField(max_length=36, null=True, default=None)
    assigned_doctor_name: str = CharField(max_length=255, null=True, default=None)
    duration_minutes: int = IntegerField(default=20, null=False)
    room: str = CharField(max_length=100, null=True, default=None)

    class Meta:
        table_name = "gws_care_appointment"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
